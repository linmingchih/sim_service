"""Generate a Sierpinski triangle fractal image based on the given depth."""
import argparse

from PIL import Image, ImageDraw


def draw_triangle(draw, points, depth):
    """Recursively draw a Sierpinski triangle."""
    if depth == 0:
        draw.polygon(points, fill='black')
    else:
        (x0, y0), (x1, y1), (x2, y2) = points
        mid01 = ((x0 + x1) // 2, (y0 + y1) // 2)
        mid12 = ((x1 + x2) // 2, (y1 + y2) // 2)
        mid20 = ((x2 + x0) // 2, (y2 + y0) // 2)
        draw_triangle(draw, [points[0], mid01, mid20], depth - 1)
        draw_triangle(draw, [mid01, points[1], mid12], depth - 1)
        draw_triangle(draw, [mid20, mid12, points[2]], depth - 1)


def main(depth):
    """Create an image canvas and generate a fractal of specified depth."""
    # Determine image size based on depth (capped for performance)
    size = 2 ** depth * 20 if depth <= 6 else 512
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    # Initial triangle vertices
    triangle = [(0, size - 1), (size - 1, size - 1), (size // 2, 0)]
    draw_triangle(draw, triangle, depth)
    output_file = 'fractal.png'
    image.save(output_file)
    print(f'Fractal image saved to {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a fractal image.')
    parser.add_argument('--depth', type=int, required=True,
                        help='Recursion depth of the fractal')
    args = parser.parse_args()
    main(args.depth)