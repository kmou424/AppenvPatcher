from config import FILE_ENCODING


class DesktopParser:
    def __init__(self):
        self.__data = {}

    def add_section(self, section):
        if section not in self.__data.keys():
            self.__data[section] = {}

    def set_pair(self, section, key, value):
        if section not in self.__data.keys():
            self.add_section(section)
        self.__data[section][key] = value

    def get_section(self, section):
        if section in self.__data.keys():
            return self.__data[section]
        return None

    def to_string(self):
        res = ""
        for sec in self.__data.keys():
            if len(self.__data[sec].keys()) == 0:
                continue
            res += "[%s]\n" % sec
            for k in self.__data[sec].keys():
                res += "%s=%s\n" % (k, self.__data[sec][k])
        return res


def load(file_path):
    with open(file_path, "r", encoding=FILE_ENCODING) as f:
        lines = [i.removesuffix("\n") for i in f.readlines()]
    desktop_parser = DesktopParser()
    cur_section = ''
    for line in lines:
        if len(line.strip()) == 0:
            continue
        if line.startswith('[') and line.endswith(']'):
            cur_section = line.removeprefix('[').removesuffix(']')
            desktop_parser.add_section(cur_section)
            continue
        if '=' in line:
            kv = [i.strip() for i in line.split('=')]
            if len(kv) < 2:
                kv.append('')
            desktop_parser.set_pair(cur_section, kv[0], kv[1])
    return desktop_parser
