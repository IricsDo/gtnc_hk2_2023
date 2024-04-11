import xlrd
from data import download_data
import pandas as pd
from os import devnull
import json
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import random
import tqdm
import math
import time
class Solution:
    def __init__(self, data_test, data_dict):
        self.data_test = data_test
        self.data_dict = data_dict
        # self.min_list = dict()
        self.max_list = dict()
        self.list_info = [key for key in list(self.data_dict.keys())]
        self.score_temp = 50
        self.get_min_max_string()
        
    def get_min_max_string(self):
        for r in self.list_info:
            # self.min_list[r] = len(min(self.data_dict[r], key=len))
            self.max_list[r] = len(max(self.data_dict[r], key=len))

    def average_score(self, s1, s2):
        return round((fuzz.partial_ratio(s1, s2) + fuzz.token_sort_ratio(s1, s2) + fuzz.token_set_ratio(s1, s2) + fuzz.ratio(s1, s2)) / 4)
        # return fuzz.ratio(s1, s2)

    def province_pre(self, input_sentence):
        r = "province"
        start_index = 0
        if len(input_sentence) - self.max_list[r] > 0 :
            start_index = len(input_sentence) - self.max_list[r]

        sub_string = input_sentence[start_index: len(input_sentence)]
        max_score = 0
        province_pre = ""
        for i in range(len(self.data_dict[r])):
            province_string = self.data_dict[r][i]
            score = self.average_score(clear_province(sub_string), remove_empty_string(province_string))
            if score > self.score_temp:
                if score > max_score:
                    max_score = score
                    province_pre = province_string

        if province_pre:
            return province_pre
        else:
            # return "*"*self.min_list[r]
            return ""


    def district_pre(self, input_sentence, province_pre):
        r = "district"
        start_index = 0
        if len(input_sentence) - self.max_list[r] - len(province_pre) > 0 :
            start_index = len(input_sentence) - self.max_list[r] - len(province_pre)

        sub_string = input_sentence[start_index: len(input_sentence) - len(province_pre)]
        max_score = 0
        district_pre = ""
        for i in range(len(self.data_dict[r])):
            district_string = self.data_dict[r][i]
            score = self.average_score(clear_district(sub_string), remove_empty_string(district_string))
            if score > self.score_temp:
                if score > max_score:
                    max_score = score
                    district_pre = district_string

        if district_pre:
            return district_pre
        else:
            # return "*"*self.min_list[r]
            return ""
        
    def ward_pre(self, input_sentence, province_pre, district_pre):
        r = "ward"
        start_index = 0
        if len(input_sentence) - self.max_list[r] - len(province_pre) - len(district_pre) > 0 :
            start_index = len(input_sentence) - self.max_list[r] - len(province_pre) - len(district_pre)

        sub_string = input_sentence[start_index: len(input_sentence) - len(province_pre) - len(district_pre)]
        max_score = 0
        ward_pre = ""
        for i in range(len(self.data_dict[r])):
            ward_string = self.data_dict[r][i]
            score = self.average_score(clear_ward(sub_string), remove_empty_string(ward_string))
            if score > self.score_temp:
                if score > max_score:
                    max_score = score
                    ward_pre = ward_string
        
        if ward_pre:
            return ward_pre
        else:
            # return "*"*self.min_list[r]
            return ""
        
    def inference(self, input_sentence):
        province_pre = self.province_pre(input_sentence)
        district_pre = self.district_pre(input_sentence, province_pre)
        ward_pre = self.ward_pre(input_sentence, province_pre, district_pre)
        print("province:", province_pre, "\tdistrict:", district_pre, "\tward:", ward_pre)

    def run(self):
        for index in range(len(self.data_test['text'])):
            self.inference(self.data_test['text'][index])

    def test_case(self):
        start_time = time.time()*1000
        test_list = ["TT Tân Bình Huyện Yên Sơn, Tuyên Quang",
                     "Nghi Sơ6n, T.X. Nghi Sơn, Thhanh Hóa",
                     "Nà Làng Phú Bình, Chiêm Hoá, Tuyên Quang",
                     "D2, Thạnh Lợi, Vĩnh Thạnh Cần Thơ",
                     "Đông Hòa,Tỉnh Phú yn",
                     "Phú Đô HuyệnPhú Lươnz"]
        test_list = ["Đông Hòa,Tỉnh Phú yn"]
        for string in test_list:
            self.inference(string)
        end_time = (time.time()*1000 - start_time) / len(test_list)
        print("--- Average %s miliseconds per %d case ---" % (end_time, len(test_list)))

def clear_province(string):
    string = remove_empty_string(string)
    string = string.replace(",", "")
    remove_string = ["Tỉnh", "Thành phố", "TP.", "T."]
    for rt in remove_string:
        if rt.lower() in string.lower():
            string = string.replace(rt, "")
        else:
            continue
    string = ''.join([i for i in string if not i.isdigit()])
    return string

def clear_district(string):
    string = remove_empty_string(string)
    string = string.replace(",", "")
    remove_string = ["Quận", "Huyện", "Thị xã", "TX.", "H.", "Q."]
    for rt in remove_string:
        if rt.lower() in string.lower():
            string = string.replace(rt, "")
        else:
            continue
    string = ''.join([i for i in string if not i.isdigit()])
    return string

def clear_ward(string):
    string = remove_empty_string(string)
    string = string.replace(",", "")
    remove_string = ["Xã", "Phường", "Thị trấn", "X.", "P.", "TT."]
    for rt in remove_string:
        if rt.lower() in string.lower():
            string = string.replace(rt, "")
        else:
            continue
    return string

def remove_empty_string(string):
    return string.replace(" ", "")

def load_json_test():
    data = None
    with open('reference/public.json', encoding='utf8') as f:
        data = json.load(f)
    return data

def load_raw_database():
    # if not download_data.check_data_exists():
    #     return
    # if not download_data.pull_data():
    #     return
    wb = xlrd.open_workbook('data/data.xls', logfile=open(devnull, 'w'))
    df = pd.read_excel(wb, dtype=str, engine='xlrd')
    return df

def load_data_run():
    remove_string = ["Tỉnh", "Thành phố", "Quận", "Huyện", "Thị xã", "Xã", "Phường", "Thị trấn"]
    dict_data = dict()
    data_file =  "data/list_ward.txt"
    with open(data_file, 'r', encoding="utf-8") as fp:
        data = fp.read().split("\n")
        new_data = []
        for line in data:
            for rt in remove_string:
                if rt.lower() in line.lower():
                    line = line.replace(rt, "")
                else:
                    continue
            new_data.append(line)
        new_data = list(filter(None, new_data))
        for data in new_data:
            tuple_temp = tuple()
            string = data.split("-")
            tuple_temp = (string[1] , string[2])
            dict_data[string[0]] = tuple_temp
    return dict_data

def remark_data_dict():
    pass

def make_database():
    database = load_raw_database()
    # dataname = ["Tỉnh Thành Phố", "Quận Huyện" , "Phường Xã"]
    province_data = database["Tỉnh Thành Phố"].to_list()
    province_data = list(set(province_data))
    file_name = r'data/list_province.txt'
    with open(file_name, 'w', encoding="utf-8") as fp:
        for item in province_data:
            fp.write("%s\n" % item)
    file_name = r'data/list_district.txt'
    with open(file_name, 'w', encoding="utf-8") as fp:
        for p in province_data:
            district_data = database.loc[database["Tỉnh Thành Phố"] == p, "Quận Huyện"].to_list()
            for item in district_data:
                fp.write("%s-%s\n" % (p, item))
    district_data = database["Quận Huyện"].to_list()
    district_data = list(set(district_data))
    file_name = r'data/list_ward.txt'
    with open(file_name, 'w', encoding="utf-8") as fp:
        for p in province_data:
            for d in district_data:
                ward_data = database.loc[(database["Tỉnh Thành Phố"] == p) & (database["Quận Huyện"] == d), "Phường Xã"].to_list()
                for item in ward_data:
                    fp.write("%s-%s-%s\n" % (p, d, item))

def main(data_test, data_dict):
    slo = Solution(data_test, data_dict)
    slo.test_case()
    # slo.run()
    
if __name__ == '__main__':
    # make_database()
    # data_test = load_json_test()
    # data_dict = load_data_run()
    # main(data_test, data_dict)