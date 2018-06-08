"""
Copyright 2018 Ryan Wick (rrwick@gmail.com)
https://github.com/rrwick/Badread

The version is stored here in a separate file so it can exist in only one place.
http://stackoverflow.com/questions/458550

This file is part of Badread. Badread is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version. Badread is distributed
in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details. You should have received a copy of the GNU General Public License along with Badread.
If not, see <http://www.gnu.org/licenses/>.
"""

import collections
import gzip
import random
import re
import sys


def get_compression_type(filename):
    """
    Attempts to guess the compression (if any) on a file using the first few bytes.
    http://stackoverflow.com/questions/13044562
    """
    magic_dict = {'gz': (b'\x1f', b'\x8b', b'\x08'),
                  'bz2': (b'\x42', b'\x5a', b'\x68'),
                  'zip': (b'\x50', b'\x4b', b'\x03', b'\x04')}
    max_len = max(len(x) for x in magic_dict)

    unknown_file = open(filename, 'rb')
    file_start = unknown_file.read(max_len)
    unknown_file.close()
    compression_type = 'plain'
    for file_type, magic_bytes in magic_dict.items():
        if file_start.startswith(magic_bytes):
            compression_type = file_type
    if compression_type == 'bz2':
        sys.exit('Error: cannot use bzip2 format - use gzip instead')
    if compression_type == 'zip':
        sys.exit('Error: cannot use zip format - use gzip instead')
    return compression_type


def get_open_func(filename):
    if get_compression_type(filename) == 'gz':
        return gzip.open
    else:  # plain text
        return open


REV_COMP_DICT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'a': 't', 't': 'a', 'g': 'c', 'c': 'g',
                 'R': 'Y', 'Y': 'R', 'S': 'S', 'W': 'W', 'K': 'M', 'M': 'K', 'B': 'V', 'V': 'B',
                 'D': 'H', 'H': 'D', 'N': 'N', 'r': 'y', 'y': 'r', 's': 's', 'w': 'w', 'k': 'm',
                 'm': 'k', 'b': 'v', 'v': 'b', 'd': 'h', 'h': 'd', 'n': 'n', '.': '.', '-': '-',
                 '?': '?'}


def complement_base(base):
    try:
        return REV_COMP_DICT[base]
    except KeyError:
        return 'N'


def reverse_complement(seq):
    return ''.join([complement_base(x) for x in seq][::-1])


def load_fastq(filename):
    reads = {}
    i = 0
    print('Loading reads', end='', file=sys.stderr, flush=True)
    with get_open_func(filename)(filename, 'rb') as fastq:
        for line in fastq:
            stripped_line = line.strip()
            if len(stripped_line) == 0:
                continue
            if not stripped_line.startswith(b'@'):
                continue
            name = stripped_line[1:].split()[0]
            sequence = next(fastq).strip()
            _ = next(fastq)
            qualities = next(fastq).strip()
            reads[name.decode()] = (sequence.decode(), qualities.decode())
            i += 1
            if i % 1000 == 0:
                print('.', end='', file=sys.stderr, flush=True)
    print('', file=sys.stderr, flush=True)
    return reads


def load_fasta(filename):
    fasta_seqs = collections.OrderedDict()
    depths, circular = {}, {}
    p = re.compile('depth=([\d\.]+)')
    with get_open_func(filename)(filename, 'rt') as fasta_file:
        name = ''
        sequence = []
        for line in fasta_file:
            line = line.strip()
            if not line:
                continue
            if line[0] == '>':  # Header line = start of new contig
                if name:
                    fasta_seqs[name.split()[0]] = ''.join(sequence)
                    sequence = []
                name = line[1:]
                short_name = name.split()[0]
                if 'depth=' in name.lower():
                    try:
                        depths[short_name] = float(p.search(name.lower()).group(1))
                    except ValueError:
                        depths[short_name] = 1.0
                else:
                    depths[short_name] = 1.0
                circular[short_name] = 'circular=true' in name.lower()
            else:
                sequence.append(line)
        if name:
            fasta_seqs[name.split()[0]] = ''.join(sequence)
    return fasta_seqs, list(depths.items()), circular


RANDOM_SEQ_DICT = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}


def get_random_base():
    """
    Returns a random base with 25% probability of each.
    """
    return RANDOM_SEQ_DICT[random.randint(0, 3)]


def get_random_different_base(b):
    random_base = get_random_base()
    while b == random_base:
        random_base = get_random_base()
    return random_base


def get_random_sequence(length):
    """
    Returns a random sequence of the given length.
    """
    return ''.join([get_random_base() for _ in range(length)])


def random_chance(chance):
    assert 0.0 <= chance <= 1.0
    return random.random() < chance


END_FORMATTING = '\033[0m'
BOLD = '\033[1m'


def bold(text):
    return BOLD + text + END_FORMATTING


def float_to_str(v, decimals=1):
    if float(int(v)) == v:
        return str(int(v))
    else:
        formatter = '%.' + str(decimals) + 'f'
        return formatter % v