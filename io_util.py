import io
import logging
import sys


def output_iterator(file_path, output_list, process=lambda x: x):
    try:
        with io.open(file_path, mode="w+", encoding="utf-8") as file:
            for line in output_list:
                file.write(process(line) + "\n")
    except IOError as error:
        logging.error("Failed to open file {0}".format(error))
        sys.exit(1)


def read_file(file_path, encoding="utf-8", preprocess=lambda x: x):
    try:
        with io.open(file_path, encoding=encoding) as file:
            for sentence in file.readlines():
                yield (preprocess(sentence))

    except IOError as err:
        logging.error("Failed to open file {0}".format(err))
        sys.exit(1)

if __name__ == '__main__':
    index = 0
    input_path = "/home/zxj/Data/SparkNotes/urls.txt"
    output_path = "/home/zxj/Data/SparkNotes/url_parts/url_part_{0}.txt"
    url_string_list = list(read_file(input_path, preprocess=lambda x: x.strip()))
    index = 0
    for i in range(0, len(url_string_list), 30):
        output_iterator(output_path.format(index), url_string_list[i: i + 30])
        index += 1