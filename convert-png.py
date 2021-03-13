from pathlib import Path
from typing import Optional
from tqdm import tqdm

NUM_PROCS=4
INKSCAPE="inkscape"
ICON_CLASSES=[ "icons", "icons-dark" ]
ICON_SIZES=[ 16, 22, 32, 48, 64, 96]

PATH_SRC=Path("./breeze-icons")
PATH_PNG=Path("./png")


def get_png_name(p: Path) -> Path:
     *_, cls, cat, size, name = p.with_suffix("").parts
     return PATH_PNG  / cls / f"{cat}-{name}_{size}.png"

def parallel_execute(commands, np: Optional[int] = None):
    if np == 1:
        for command in tqdm(commands):
            run_command(command)
    else:
        from multiprocessing.pool import ThreadPool
        import subprocess

        def run_command(cmd):
            try:
                res = subprocess.run(cmd)
                return res.returncode
            except Exception as e:
                print(e)
                return 0

        tp = ThreadPool(np)
        gen = tp.imap_unordered(run_command, commands, chunksize=1)
        for r in tqdm(gen, total=len(commands), smoothing=0.1):
            pass
        tp.close()
        tp.join()


def update_conversions():
    svg_files = []
    for cls in ICON_CLASSES:
        pclass = PATH_PNG / cls
        pclass.mkdir(parents=True, exist_ok=True)
        sclass = PATH_SRC / cls
        for size in ICON_SIZES:
            svg_files += sclass.glob(f"*/{size}/*.svg")
    png_files = [get_png_name(f) for f in svg_files]
    commands = []
    for svg, png in zip(svg_files, png_files):
        sstat = svg.stat()
        if sstat.st_size <= 50:
            continue
        with svg.open("rt") as t:
            if "<svg" not in t.read(500):
                continue
        if not png.exists() or (png.stat().st_mtime < sstat.st_mtime):
            commands.append((INKSCAPE, "-z",  "-b", "#FF00FF", "-y", "0", str(svg), "-e", str(png)))
    print(len(commands), " new conversions found")
    if len(commands):
        parallel_execute(commands, NUM_PROCS)

def update_index():
    files = PATH_PNG.glob("**/*.png")
    filelist = "\n".join(str(f.relative_to(PATH_PNG).with_suffix("").as_posix()) for f in files)
    with open("index.template.html", "rt") as tpl:
        with open("index.html", "wt") as html:
            s = tpl.read()
            s = s.replace("$$$FULL_DIR_TREE$$$", filelist)
            html.write(s)
    print("index updated")

if __name__ == "__main__":
    update_conversions()
    update_index()
