from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "figures" / "architecture.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "arialbd.ttf" if bold else "arial.ttf"
    candidates = [
        Path("C:/Windows/Fonts") / filename,
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], lines: list[str], *, fill: str, size: int, bold: bool = False) -> None:
    selected_font = font(size, bold)
    line_height = size + 10
    y = box[1] + ((box[3] - box[1]) - line_height * len(lines)) / 2
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=selected_font)
        width = bounds[2] - bounds[0]
        draw.text(((box[0] + box[2] - width) / 2, y), line, font=selected_font, fill=fill)
        y += line_height


def rounded_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, subtitle: str, *, planned: bool = False) -> None:
    outline = "#C77700" if planned else "#176B73"
    fill = "#FFF5E7" if planned else "#EAF5F5"
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=outline, width=5)
    centered(draw, (box[0], box[1] + 10, box[2], box[1] + 76), [title], fill="#17343A", size=28, bold=True)
    centered(draw, (box[0] + 18, box[1] + 65, box[2] - 18, box[3] - 8), subtitle.split("\n"), fill="#38555B", size=21)
    if planned:
        draw.text((box[2] - 142, box[1] + 14), "PLANEJADO", font=font(15, True), fill="#9B5A00")


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], *, planned: bool = False) -> None:
    color = "#C77700" if planned else "#176B73"
    width = 5
    if planned:
        x1, y1 = start
        x2, y2 = end
        parts = 10
        for index in range(parts):
            if index % 2 == 0:
                a = index / parts
                b = (index + 1) / parts
                draw.line((x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), fill=color, width=width)
    else:
        draw.line((*start, *end), fill=color, width=width)
    x, y = end
    draw.polygon([(x, y), (x - 13, y - 18), (x + 13, y - 18)], fill=color)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1600, 940), "#F8FAFA")
    draw = ImageDraw.Draw(image)

    draw.text((90, 45), "Arquitetura da solução", font=font(42, True), fill="#17343A")
    draw.text((90, 102), "Versão parcial validada e evolução prevista", font=font(25), fill="#597075")

    user = (600, 160, 1000, 280)
    dashboard = (535, 345, 1065, 500)
    api = (535, 575, 1065, 730)
    database = (90, 790, 555, 915)
    rules = (595, 790, 1060, 915)
    planned = (1100, 575, 1535, 730)

    rounded_box(draw, user, "Usuário", "Analista ou gestor comercial")
    rounded_box(draw, dashboard, "Dashboard web", "HTML, CSS e JavaScript\nindicadores, funil e fila priorizada")
    rounded_box(draw, api, "API de aplicação", "FastAPI / JSON\nmétricas, filtros e regras de negócio")
    rounded_box(draw, database, "Dados", "CSV público fictício + SQLite\nimportação idempotente")
    rounded_box(draw, rules, "Priorização auditável", "regras transparentes no produto\nML mantido como experimento")
    rounded_box(draw, planned, "Evolução", "PostgreSQL/Supabase, autenticação\ne assistente por funções controladas", planned=True)

    arrow(draw, (800, 280), (800, 345))
    arrow(draw, (800, 500), (800, 575))
    arrow(draw, (660, 730), (330, 790))
    arrow(draw, (930, 730), (825, 790))
    arrow(draw, (1065, 652), (1100, 652), planned=True)

    draw.line((1120, 845, 1190, 845), fill="#176B73", width=5)
    draw.text((1205, 830), "Implementado", font=font(19), fill="#38555B")
    for start_x in range(1120, 1190, 18):
        draw.line((start_x, 885, min(start_x + 10, 1190), 885), fill="#C77700", width=5)
    draw.text((1205, 870), "Planejado", font=font(19), fill="#38555B")

    image.save(OUTPUT, format="PNG", optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
