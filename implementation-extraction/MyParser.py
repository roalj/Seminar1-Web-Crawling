from abc import ABC
from html.parser import HTMLParser
import re

TYPE_START = "start"
TYPE_END = "end"
TYPE_DATA = "data"

class MyHTMLParser(HTMLParser, ABC):

    def __init__(self):
        super().__init__()
        self.page_content = []
        self.page_trash = []

    def handle_starttag(self, tag, attrs):
        self.page_content.append(DataTag(tag, TYPE_START, attrs))

    def handle_endtag(self, tag):
        self.page_content.append(DataTag(tag, TYPE_END, None))

    def handle_data(self, data):
        if not "".__eq__(data) and not data.isspace():
            data = self.remove_spaces_new_line(data)
            self.page_content.append(DataTag(data, TYPE_DATA, None))
        else:
            self.page_trash.append(data)

    @staticmethod
    def remove_spaces_new_line(data):
        regex = r'\s+'
        return re.sub(regex, " ", data)



class DataTag:
    def __init__(self, name, type, attrs):
        self.name = name
        self.type = type
        self.attrs = attrs

    def __eq__(self, other):
        #if self.type == TYPE_START:
            #if "body" in self.name:
            #   return self.name == other.name and self.type == other.type
        if self is None or other is None:
            return False
        return self.name == other.name and self.type == other.type and self.attrs == other.attrs

    def is_data_type(self):
        return self.type == TYPE_DATA

    def is_start_type(self):
        return self.type == TYPE_START

    def is_end_type(self):
        return self.type == TYPE_END

    def is_same_start_tag(self, y):
        return self.name == y.name

    def is_same_data_tag(self, y):
        return self.name == y.name

    def __str__(self):
        if self.type == TYPE_DATA:
            return self.name
        elif self.type == TYPE_START:
            return '<' + self.name + '>'
        elif self.type == TYPE_END:
            return '<' + self.name + '/>\n'


class DifferentLines:
    def __init__(self, line, parse_content):
        self.line = line
        self.parse_content = parse_content
        self.attr_remove = []
    def __str__(self):
        return self.line

    def get_first_content(self):
        for x in self.parse_content:
            if x.is_data_type():
                return x
        return None

    def get_all_start_tags(self):
        start_tags = []
        for x in self.parse_content:
            if x.is_start_type():
                start_tags.append(x)
        return start_tags

    def get_lowest_len(self, str1, str2):
        if len(str1) < len(str2):
            return len(str1)
        return len(str2)

    def num_of_common_chars(self, _str1, _str2):
        n = self.get_lowest_len(_str1, _str2)
        count = 0
        for i in range(n):
            if _str1[i] == _str2[i]:
                count += 1
            else:
                return count
        return count

    def compare_attr(self, attrs1, attrs2):
        diff_attr = []
        if len(attrs1) == len(attrs2):
            for i in range(len(attrs1)):
                A = attrs1[i]
                B = attrs2[i]
                if len(A) > 1 and len(B) > 1:
                    if A[0] == B[0] and A[1] != B[1]:
                        num_comm = self.num_of_common_chars(A[1], B[1])
                        if len(A[1]) != num_comm:
                            diff_attr.append((A[1], A[1][:num_comm]))
        return diff_attr

    def compare_start_tags(self, diff2):
        diff_attributs = []
        tags1 = self.get_all_start_tags()
        tags2 = diff2.get_all_start_tags()
        if len(tags1) == len(tags2):  #imata enako start tagov
            for i in range(len(tags1)):
                diff_attributs += self.compare_attr(tags1[i].attrs, tags2[i].attrs)
                #if tags1[0] == "class"
        return diff_attributs


#test
"""class MyHTMLParser1(HTMLParser, ABC):

    def __init__(self, pairs):
        super().__init__()
        self.page_content = []
        self.page_trash = []
        self.previous_start_tag = None
        self.pairs = pairs

    def handle_starttag(self, tag, attrs):
        self.page_content.append(DataTag(tag, TYPE_START, attrs))
        self.previous_start_tag = DataTag(tag, TYPE_START, attrs)

    def handle_endtag(self, tag):
        self.page_content.append(DataTag(tag, TYPE_END, None))

    def handle_data(self, data):
        if not "".__eq__(data) and not data.isspace():
            data = self.remove_spaces_new_line(data)
            data_tag = DataTag(data, TYPE_DATA, None)
            self.page_content.append(data_tag)
        else:
            self.page_trash.append(data)

    def is_data_different(self, data):
        for a in self.pairs:
            if a.is_same_data_tag(data):
                1


    @staticmethod
    def remove_spaces_new_line(data):
        regex = r'\s+'
        return re.sub(regex, " ", data)
"""




