"""Cascade multiple 4-port Touchstone networks into a single network."""
import argparse
import skrf as rf


def generate_chain(n: int, path: str):
    """Cascade `n` identical 4-port networks from the given Touchstone file."""
    if n < 1:
        raise ValueError("n must be >= 1")
    base = rf.Network(path)
    if base.nports != 4:
        raise ValueError("Touchstone must be a 4-port file")
    chain = base
    for _ in range(1, n):
        next_net = rf.Network(path)
        chain = rf.connect(chain, 2, next_net, 0, 2)
    chain.write_touchstone('full_channel')


def main(file_path: str, n: int):
    generate_chain(n, file_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate cascaded 4-port network')
    parser.add_argument('--file', required=True,
                        help='Input 4-port Touchstone file')
    parser.add_argument('--n', type=int, required=True,
                        help='Number of sections in the chain')
    args = parser.parse_args()
    main(args.file, args.n)
