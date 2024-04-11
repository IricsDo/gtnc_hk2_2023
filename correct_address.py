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
import numpy as np
from unidecode import unidecode
from mongomock import MongoClient
import unicodedata

# Reference https://gist.github.com/phineas-pta/05cad38a29fea000ab6d9e13a6f7e623
BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)

def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)
# End reference
class Solution:
    def __init__(self, data_test, data_dict):
        self.data_test = data_test
        self.data_dict = data_dict
        self.min_list = dict()
        self.max_list = dict()
        self.list_info = [key for key in list(self.data_dict.keys())]
        self.score_temp = 50
        self.client = MongoClient()
        self.address_classification = self.client.address_classification
        self.province_db = self.address_classification.province
        self.district_db = self.address_classification.district
        self.ward_db = self.address_classification.ward
        self.get_min_max_string()
        
        with open('data/tinh_tp.json', 'r',  encoding='utf8') as file:
            data = json.load(file)
        for document in data.values():
            self.province_db.insert_one(document)
        
        with open('data/quan_huyen.json', 'r',  encoding='utf8') as file:
            data = json.load(file)
        for document in data.values():
            self.district_db.insert_one(document)

        with open('data/xa_phuong.json', 'r',  encoding='utf8') as file:
            data = json.load(file)
        for document in data.values():
            self.ward_db.insert_one(document)
        # Load the provinces
        self.provinces = self.get_provinces()


    def get_min_max_string(self):
        for r in self.list_info:
            self.min_list[r] = len(min(self.data_dict[r].values(), key=len))
            self.max_list[r] = len(max(self.data_dict[r].values(), key=len))

    def average_score(self, s1, s2):
        # return round((fuzz.partial_ratio(s1, s2) + fuzz.token_sort_ratio(s1, s2) + fuzz.token_set_ratio(s1, s2) + fuzz.ratio(s1, s2)) / 4)
        return fuzz.ratio(s1, s2)

    def levenshtein_distance(self, word1: str, word2: str):
        """Calculate the levenshtein distance between two strings.

        Args:
            word1 (str): string from input text. 
                Should be string without blankspace between words, without diacritical marks.
                For example: 'TP. Hồ Chí Minh' should be 'tphochiminh'.
            word2 (str): string from predefined dataset.

        Returns:
            int: an integer value represents the distance.
                The smaller the value, the more similar the two strings are.
                In the best case, distance=0 indicates that two strings are identical.
        """
        # word1 as the row
        size_row = len(word1) + 1
        # word2 as the column
        size_col = len(word2) + 1
        # Initiate matrix of zeros
        distances = np.zeros((size_row, size_col), dtype=int)

        for x in range(size_row):
            distances[x][0] = x
        for y in range(size_col):
            distances[0][y] = y
        
        for x in range(1, size_row):
            for y in range(1, size_col):
                if word1[x-1] == word2[y-1]:
                    distances[x][y] = distances[x-1][y-1]
                else:
                    distances[x][y] = min(
                        distances[x-1][y]+1,
                        distances[x-1][y-1]+1,
                        distances[x][y-1]+1
                    )
        return distances[size_row-1][size_col-1]
    
    def find_min_distance(self, distances: dict):
        # Input a dict of distance and province code
        # for example, distances = {'01': 0.5, '02': 1}
        # output the province code
        return min(distances, key=distances.get)
    
    def get_provinces(self):
        provinces = []
        result = self.province_db.find({}, {'slug': True, 'code': True})
        for province in result:
            provinces.append(province)
        return provinces

    def get_districts(self, province_code):
        districts = []
        result = self.district_db.find({'parent_code': province_code}, {'slug': True, 'code': True, 'parent_code': True})
        for district in result:
            districts.append(district)
        return districts

    def get_wards(self, district_code):
        wards = []
        result = self.ward_db.find({'parent_code': district_code}, {'slug': True, 'code': True, 'parent_code': True})
        for ward in result:
            wards.append(ward)
        return wards
    
    def get_all_provinces(self):
        provinces = list()
        return provinces
    
    def get_all_districts(self):
        districts = list()
        districts = self.data_dict['district'].values()
        districts = list(set(districts))
        temp = districts
        districts = []
        for t in temp:
            districts.append(xoa_dau(t).replace(" ", "").lower())
        return districts
    
    def get_all_wards(self):
        wards = list()
        wards = self.data_dict['ward'].values()
        wards = list(set(wards))
        temp = wards
        wards = []
        for t in temp:
            wards.append(xoa_dau(t).replace(" ", "-").lower())
        return wards
    
    def get_matched_province(self, province_code):
        return self.province_db.find_one({'code': province_code})['name']

    def get_matched_district(self, district_code):
        return self.district_db.find_one({'code': district_code})['name']

    def get_matched_ward(self, ward_code):
        return self.ward_db.find_one({'code': ward_code})['name']
    
    def province_pre(self, input_sentence):
        r = "province"
        start_index = 0
        if len(input_sentence) - self.max_list[r] > 0 :
            start_index = len(input_sentence) - self.max_list[r]

        sub_string = input_sentence[start_index: len(input_sentence)]
        matched_provine_name = None
        matched_province_code = None
        all_province_distances = {}
        for province in self.provinces:
            distance = self.levenshtein_distance(clear_province(sub_string), province['slug'].replace('-', ''))
            all_province_distances[province['code']] = distance
        matched_province_code = self.find_min_distance(all_province_distances)
        if matched_province_code == None:
            matched_provine_name = ''
        else:
            matched_provine_name = self.get_matched_province(matched_province_code)
        # max_score = 0
        # province_pre = ""
        # for i in range(len(self.data_dict[r])):
        #     province_string = self.data_dict[r][i]
        #     score = self.average_score(clear_province(sub_string), remove_empty_string(province_string))
        #     if score > self.score_temp:
        #         if score > max_score:
        #             max_score = score
        #             province_pre = province_string
        if matched_provine_name:
            return matched_provine_name, matched_province_code
        else:
            # return "*"*self.min_list[r]
            return "", None


    def district_pre(self, input_sentence, matched_provine_name, matched_province_code):
        r = "district"
        start_index = 0
        if len(input_sentence) - self.max_list[r] - len(matched_provine_name) > 0 :
            start_index = len(input_sentence) - self.max_list[r] - len(matched_provine_name)

        sub_string = input_sentence[start_index: len(input_sentence) - len(matched_provine_name)]
        matched_district_name = None
        matched_district_code = None
        districts = list()
        all_district_distances = {}
        if matched_province_code:
            districts = self.get_districts(matched_province_code)
            for district in districts:
                distance = self.levenshtein_distance(clear_district(sub_string), district['slug'].replace('-', ''))
                all_district_distances[district['code']] = distance
            matched_district_code = self.find_min_distance(all_district_distances)
        else:
            districts = self.get_all_districts()

        if matched_district_code == None:
            matched_district_name = ''
        else:
            matched_district_name = self.get_matched_district(matched_district_code)


        # max_score = 0
        # district_pre = ""
        # for i in range(len(self.data_dict[r])):
        #     district_string = self.data_dict[r][i]
        #     score = self.average_score(clear_district(sub_string), remove_empty_string(district_string))
        #     if score > self.score_temp:
        #         if score > max_score:
        #             max_score = score
        #             district_pre = district_string

        if matched_district_name:
            return matched_district_name, matched_district_code
        else:
            # return "*"*self.min_list[r]
            return "", None
        
    def ward_pre(self, input_sentence, matched_provine_name, matched_district_name, matched_district_code):
        r = "ward"
        start_index = 0
        if len(input_sentence) - self.max_list[r] - len(matched_provine_name) - len(matched_district_name) > 0 :
            start_index = len(input_sentence) - self.max_list[r] - len(matched_provine_name) - len(matched_district_name)

        sub_string = input_sentence[start_index: len(input_sentence) - len(matched_provine_name) - len(matched_district_name)]
        matched_ward_name = None
        matched_ward_code = None
        wards = list()
        all_wards_distances = {}
        if matched_district_code:
            wards = self.get_wards(matched_district_code)
            for ward in wards:
                distance = self.levenshtein_distance(sub_string, ward['slug'].replace('-', ''))
                all_wards_distances[ward['code']] = distance
            matched_ward_code = self.find_min_distance(all_wards_distances)
        else:
            wards = self.get_all_wards()

        if matched_ward_code == None:
            matched_ward_name = ''
        else:
            matched_ward_name = self.get_matched_ward(matched_ward_code)

        # max_score = 0
        # ward_pre = ""
        # for i in range(len(self.data_dict[r])):
        #     ward_string = self.data_dict[r][i]
        #     score = self.average_score(clear_ward(sub_string), remove_empty_string(ward_string))
        #     if score > self.score_temp:
        #         if score > max_score:
        #             max_score = score
        #             ward_pre = ward_string
        
        if matched_ward_name:
            return matched_ward_name
        else:
            # return "*"*self.min_list[r]
            return ""
        
    def process(self, input_sentence):
        matched_provine_name,  matched_province_code= self.province_pre(input_sentence)
        matched_district_name,  matched_district_code = self.district_pre(input_sentence, matched_provine_name, matched_province_code)
        matched_ward_name = self.ward_pre(input_sentence, matched_provine_name, matched_district_name, matched_district_code)
        return {
            "province": matched_provine_name,
            "district": matched_district_name,
            "ward": matched_ward_name,
        }
    
    def run(self):
        for index in range(len(self.data_test['text'])):
            self.process(self.data_test['text'][index])

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
            print(self.process(string))
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
    return string.lower()

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
    return string.lower()

def clear_ward(string):
    string = remove_empty_string(string)
    string = string.replace(",", "")
    remove_string = ["Xã", "Phường", "Thị trấn", "X.", "P.", "TT."]
    for rt in remove_string:
        if rt.lower() in string.lower():
            string = string.replace(rt, "")
        else:
            continue
    return string.lower()

def remove_empty_string(string):
    return string.replace(" ", "")

def load_json_test():
    data = None
    with open('reference/public.json', encoding='utf8') as f:
        data = json.load(f)
    return data

# def load_raw_database():
    # if not download_data.check_data_exists():
    #     return
    # if not download_data.pull_data():
    #     return
    # wb = xlrd.open_workbook('data/data.xls', logfile=open(devnull, 'w'))
    # df = pd.read_excel(wb, dtype=str, engine='xlrd')
    # return df

def load_data_run():
    remove_string = ["Tỉnh", "Thành phố", "Quận", "Huyện", "Thị xã", "Xã", "Phường", "Thị trấn"]
    province_dict = dict()
    district_dict = dict()
    ward_dict = dict()
    data_file =  "data/list_ward.txt"
    with open(data_file, 'r', encoding="utf-8") as fp:
        data = fp.read().split("\n")
        new_data = []
        for _, line in enumerate(data):
            for rt in remove_string:
                if rt.lower() in line.lower():
                    line = line.replace(rt, "")
                else:
                    continue
            new_data.append(line)
        new_data = list(filter(None, new_data))
        for index, data in enumerate(new_data):
            string = data.split("-")
            province_dict[index] = string[0].strip()
            district_dict[index] = string[1].strip()
            ward_dict[index] = string[2].strip()


    return {'province' : province_dict, 'district' : district_dict, 'ward' : ward_dict}

# def make_database():
#     database = load_raw_database()
#     # dataname = ["Tỉnh Thành Phố", "Quận Huyện" , "Phường Xã"]
#     province_data = database["Tỉnh Thành Phố"].to_list()
#     province_data = list(set(province_data))
#     file_name = r'data/list_province.txt'
#     with open(file_name, 'w', encoding="utf-8") as fp:
#         for item in province_data:
#             fp.write("%s\n" % item)
#     file_name = r'data/list_district.txt'
#     with open(file_name, 'w', encoding="utf-8") as fp:
#         for p in province_data:
#             district_data = database.loc[database["Tỉnh Thành Phố"] == p, "Quận Huyện"].to_list()
#             for item in district_data:
#                 fp.write("%s-%s\n" % (p, item))
#     district_data = database["Quận Huyện"].to_list()
#     district_data = list(set(district_data))
#     file_name = r'data/list_ward.txt'
#     with open(file_name, 'w', encoding="utf-8") as fp:
#         for p in province_data:
#             for d in district_data:
#                 ward_data = database.loc[(database["Tỉnh Thành Phố"] == p) & (database["Quận Huyện"] == d), "Phường Xã"].to_list()
#                 for item in ward_data:
#                     fp.write("%s-%s-%s\n" % (p, d, item))

def main(data_test, data_dict):
    slo = Solution(data_test, data_dict)
    slo.test_case()
    # slo.run()
if __name__ == '__main__':
    # make_database()
    data_test = load_json_test()
    data_dict = load_data_run()
    main(data_test, data_dict)
