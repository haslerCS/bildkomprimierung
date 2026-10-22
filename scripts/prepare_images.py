#!/usr/bin/env python3
"""Stage responsive image candidates without changing a web project."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

try:
    from PIL import Image, ImageOps, features
except ImportError as exc:
    raise SystemExit("Pillow fehlt. Installiere scripts/requirements.txt in einer isolierten venv.") from exc


DEFAULT_WIDTHS = (320, 640, 960, 1280, 1920)
SUPPORTED = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
OTHER_IMAGES = {".svg", ".gif", ".avif", ".apng", ".tif", ".tiff", ".bmp", ".ico", ".heic"}
GENERATED_NAME = re.compile(r"--(?:jpg|jpeg|png|webp)--\d+w\.(?:jpg|jpeg|png|webp)$", re.I)
RIGHTS_TAGS = ("Copyright", "Rights", "UsageTerms", "Artist", "Creator", "WebStatement")


def inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def metadata(path: Path, exiftool: str) -> dict:
    result = subprocess.run(
        [exiftool, "-json", *[f"-{tag}" for tag in RIGHTS_TAGS], str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)[0]


def preserve_rights(source: Path, target: Path, source_metadata: dict, exiftool: str) -> None:
    populated = [tag for tag in RIGHTS_TAGS if source_metadata.get(tag)]
    if populated:
        result = subprocess.run(
            [exiftool, "-overwrite_original", "-TagsFromFile", str(source),
             *[f"-{tag}" for tag in populated], str(target)],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise ValueError(f"Copyright-Metadaten konnten nicht bewahrt werden: {result.stderr.strip()}")

        target_metadata = metadata(target, exiftool)
        for tag in populated:
            if str(source_metadata[tag]) != str(target_metadata.get(tag)):
                raise ValueError(f"Copyright-Metadatum {tag} fehlt in {target.name}")

    gps = subprocess.run(
        [exiftool, "-json", "-GPS:All", str(target)],
        check=True, capture_output=True, text=True,
    )
    gps_fields = set(json.loads(gps.stdout)[0]) - {"SourceFile"}
    if gps_fields:
        raise ValueError(f"GPS-Metadaten blieben in {target.name}: {sorted(gps_fields)}")


def save_image(image: Image.Image, target: Path, fmt: str, kind: str, icc: bytes | None,
               source: Path, source_metadata: dict, exiftool: str) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    options: dict = {}
    if icc:
        options["icc_profile"] = icc
    if fmt == "JPEG":
        options.update(quality=95 if kind == "graphic" else 88, optimize=True, progressive=True)
    elif fmt == "PNG":
        options.update(optimize=True)
    elif fmt == "WEBP":
        options.update(method=6, lossless=kind == "graphic",
                       quality=100 if kind == "graphic" else 88)
    try:
        image.save(target, format=fmt, **options)
        preserve_rights(source, target, source_metadata, exiftool)
        with Image.open(target) as check:
            if check.size != image.size or getattr(check, "n_frames", 1) != 1:
                raise ValueError(f"Ausgabe hat falsche Abmessungen oder ist animiert: {target}")
            if icc and not check.info.get("icc_profile"):
                raise ValueError(f"Farbprofil fehlt in {target.name}")
        return target.stat().st_size
    except Exception:
        target.unlink(missing_ok=True)
        raise


def output_record(path: Path, staging: Path, fmt: str, width: int, height: int,
                  byte_count: int, compared_with: int | None = None) -> dict:
    record = {
        "staged_path": str(path),
        "relative_output": str(path.relative_to(staging)),
        "format": fmt.lower(),
        "width": width,
        "height": height,
        "bytes": byte_count,
    }
    if compared_with is not None:
        record["comparison_bytes"] = compared_with
        record["saving_percent"] = round(100 * (1 - byte_count / compared_with), 2)
    return record


def widths_for(relative: str, source_width: int, width_map: dict) -> list[int]:
    widths = width_map.get(relative, DEFAULT_WIDTHS)
    if not isinstance(widths, (list, tuple)) or any(type(item) is not int or item <= 0 for item in widths):
        raise ValueError(f"Ungültige Breiten für {relative}")
    return sorted({width for width in widths if width <= source_width} | {source_width})


def prepare_one(source: Path, project: Path, staging: Path, width_map: dict,
                kind_map: dict, exiftool: str) -> dict:
    relative = source.relative_to(project).as_posix()
    original_bytes = source.stat().st_size
    kind = kind_map.get(relative, "graphic" if source.suffix.lower() == ".png" else "photo")
    with Image.open(source) as opened:
        expected = SUPPORTED[source.suffix.lower()]
        if opened.format != expected:
            raise ValueError(f"Dateiendung und Bildformat stimmen nicht überein ({opened.format})")
        if getattr(opened, "n_frames", 1) != 1 or getattr(opened, "is_animated", False):
            raise ValueError("animiertes Bild")
        if opened.mode in {"CMYK", "I;16", "I;16B", "I;16L", "F"}:
            raise ValueError(f"Farbmodus {opened.mode} braucht eine gesonderte Farbprüfung")
        original_info = opened.info.copy()
        image = ImageOps.exif_transpose(opened)
        image.load()

    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA" if "transparency" in original_info else "RGB")
    if source.suffix.lower() in {".jpg", ".jpeg"} and image.mode != "RGB":
        image = image.convert("RGB")

    icc = original_info.get("icc_profile")
    source_metadata = metadata(source, exiftool)
    ext = source.suffix.lower().lstrip(".")
    parent = staging / source.relative_to(project).parent
    source_width, source_height = image.size
    variants = []
    rejected = []

    for width in widths_for(relative, source_width, width_map):
        height = max(1, round(source_height * width / source_width))
        resized = image if width == source_width else image.resize((width, height), Image.Resampling.LANCZOS, reducing_gap=3)
        base_bytes = original_bytes

        if expected in {"JPEG", "PNG"} and width < source_width:
            fallback = parent / f"{source.stem}--{ext}--{width}w.{ext}"
            fallback_bytes = save_image(resized, fallback, expected, kind, icc, source, source_metadata, exiftool)
            base_bytes = fallback_bytes
            if fallback_bytes < original_bytes:
                variants.append(output_record(fallback, staging, expected, width, height,
                                              fallback_bytes, original_bytes))
            else:
                rejected.append({"variant": str(fallback.relative_to(staging)),
                                 "reason": "nicht kleiner als das Original", "bytes": fallback_bytes})
                fallback.unlink(missing_ok=True)

        webp = parent / f"{source.stem}--{ext}--{width}w.webp"
        webp_bytes = save_image(resized, webp, "WEBP", kind, icc, source, source_metadata, exiftool)
        qualifies = webp_bytes <= base_bytes * 0.9 and webp_bytes < original_bytes
        if qualifies:
            variants.append(output_record(webp, staging, "WEBP", width, height,
                                          webp_bytes, base_bytes))
        else:
            rejected.append({"variant": str(webp.relative_to(staging)),
                             "reason": "weniger als 10 % Ersparnis oder größer als das Original",
                             "bytes": webp_bytes, "comparison_bytes": base_bytes})
            webp.unlink(missing_ok=True)

    return {
        "source": relative,
        "sha256": digest(source),
        "format": expected.lower(),
        "kind": kind,
        "width": source_width,
        "height": source_height,
        "bytes": original_bytes,
        "variants": variants,
        "rejected": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--width-map", type=Path, help="JSON: projekt-relative Quelldatei -> gewünschte Breiten")
    parser.add_argument("--kind-map", type=Path, help="JSON: projekt-relative Quelldatei -> photo oder graphic")
    args = parser.parse_args()

    project = args.project_root.resolve(strict=True)
    folder = args.folder.resolve(strict=True)
    staging = args.staging.resolve()
    plan_path = args.plan.resolve()
    if not project.is_dir() or not folder.is_dir() or not inside(folder, project):
        parser.error("Der Bildordner muss innerhalb der Projektwurzel liegen.")
    if inside(staging, project) or inside(plan_path, project) or inside(plan_path, staging):
        parser.error("Staging und Plan müssen außerhalb des Webprojekts und getrennt liegen.")
    if staging.exists() and any(staging.iterdir()):
        parser.error("Der Staging-Ordner muss leer sein.")
    if not features.check("webp"):
        parser.error("Diese Pillow-Installation unterstützt WebP nicht.")
    exiftool = shutil.which("exiftool")
    if not exiftool:
        parser.error("ExifTool fehlt; installiere es lokal, bevor Bilder verarbeitet werden.")

    width_map = {}
    if args.width_map:
        width_map = json.loads(args.width_map.read_text(encoding="utf-8"))
        if not isinstance(width_map, dict):
            parser.error("Die Breitenzuordnung muss ein JSON-Objekt sein.")
    kind_map = {}
    if args.kind_map:
        kind_map = json.loads(args.kind_map.read_text(encoding="utf-8"))
        if not isinstance(kind_map, dict) or any(value not in {"photo", "graphic"} for value in kind_map.values()):
            parser.error("Die Bildart-Zuordnung muss photo oder graphic je Quelldatei enthalten.")

    owned_outputs = set()
    manifest_path = project / ".bildkomprimierung-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("images", []):
            owned_outputs.update(item.get("outputs", []))

    staging.mkdir(parents=True, exist_ok=True)
    warnings.simplefilter("error", Image.DecompressionBombWarning)
    images = []
    skipped = []
    for source in sorted(folder.rglob("*")):
        if source.is_symlink() or not source.is_file():
            continue
        suffix = source.suffix.lower()
        relative = source.relative_to(project).as_posix()
        if relative in owned_outputs:
            continue
        if GENERATED_NAME.search(source.name):
            skipped.append({"source": relative,
                            "reason": "wirkt wie eine erzeugte Variante, steht aber nicht im Manifest; manuell prüfen"})
            continue
        if suffix in OTHER_IMAGES:
            skipped.append({"source": relative, "reason": "nicht unterstütztes Format oder Animation"})
            continue
        if suffix not in SUPPORTED:
            continue
        try:
            images.append(prepare_one(source, project, staging, width_map, kind_map, exiftool))
        except Exception as exc:
            skipped.append({"source": relative, "reason": str(exc)})

    plan = {
        "schema_version": 1,
        "project_root": str(project),
        "selected_folder": str(folder),
        "staging": str(staging),
        "images": images,
        "skipped": skipped,
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"images": len(images), "variants": sum(len(item["variants"]) for item in images),
                      "skipped": len(skipped), "plan": str(plan_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
