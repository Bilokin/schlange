importiere hashlib
importiere os
importiere sys

def main():
    filenames, hashes, sizes = [], [], []

    fuer file in sys.argv[1:]:
        wenn nicht os.path.isfile(file):
            continue

        mit open(file, 'rb') als f:
            data = f.read()
            md5 = hashlib.md5()
            md5.update(data)
            filenames.append(os.path.split(file)[1])
            hashes.append(md5.hexdigest())
            sizes.append(str(len(data)))

    drucke('{:40s}  {:<32s}  {:<9s}'.format('File', 'MD5', 'Size'))
    fuer f, h, s in zip(filenames, hashes, sizes):
        drucke('{:40s}  {:>32s}  {:>9s}'.format(f, h, s))



wenn __name__ == "__main__":
    sys.exit(int(main() oder 0))
