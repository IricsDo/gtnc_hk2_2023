import xlrd
import xlsxwriter
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
    def __init__(self):
        self.client = MongoClient()
        self.address_classification = self.client.address_classification
        self.province_db = self.address_classification.province
        self.district_db = self.address_classification.district
        self.ward_db = self.address_classification.ward

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
        if province_code:
            result = self.district_db.find({'parent_code': province_code}, {'slug': True, 'code': True, 'parent_code': True})
        else:
            result = self.district_db.find({}, {'slug': True, 'code': True, 'parent_code': True})
        for district in result:
            districts.append(district)
        return districts

    def get_wards(self, district_code):
        wards = []
        if district_code:
            result = self.ward_db.find({'parent_code': district_code}, {'slug': True, 'code': True, 'parent_code': True})
        else:
            result = self.ward_db.find({}, {'slug': True, 'code': True, 'parent_code': True})
        for ward in result:
            wards.append(ward)
        return wards
    
    def get_matched_province(self, province_code):
        return self.province_db.find_one({'code': province_code})['name']

    def get_matched_district(self, district_code):
        return self.district_db.find_one({'code': district_code})['name']

    def get_matched_ward(self, ward_code):
        return self.ward_db.find_one({'code': ward_code})['name']
    
    def province_pre(self, input_sentence):
        input_sentence = clear_sub_string(input_sentence)
        # print("input_province", input_sentence)
        matched_provine_name = None
        matched_province_code = None
        is_break = False
        provinces = self.get_provinces()
        sub_string = ""
        for index in range(2,len(input_sentence), 1):
            sub_string = input_sentence[len(input_sentence) - index: len(input_sentence)]
            all_province_distances = {}
            for province in provinces:
                data = province['slug'].replace('-', '')
                if fuzz.token_sort_ratio(sub_string,data) > 85: # random number :))
                    is_break = True
                distance = self.levenshtein_distance(sub_string, data)
                all_province_distances[province['code']] = distance
            matched_province_code = self.find_min_distance(all_province_distances)
            if matched_province_code == None or not is_break:
                matched_provine_name = ''
            else:
                matched_provine_name = self.get_matched_province(matched_province_code)
            if is_break:
                break

        if matched_provine_name:
            return matched_provine_name, matched_province_code, input_sentence[:len(input_sentence) - len(sub_string)]
        else:
            return "", None, input_sentence


    def district_pre(self, input_sentence, matched_province_code):
        # print("input_district", input_sentence)
        matched_district_name = None
        matched_district_code = None
        is_break = False
        districts = self.get_districts(matched_province_code)
        sub_string = ""
        for index in range(2, len(input_sentence), 1):
            sub_string = input_sentence[len(input_sentence) - index: len(input_sentence)]
            all_district_distances = {}
            for district in districts:
                data = district['slug'].replace('-', '')
                if fuzz.token_sort_ratio(sub_string,data) > 80: #  magic number :)) 
                    is_break = True
                distance = self.levenshtein_distance(sub_string, data)
                all_district_distances[district['code']] = distance
            matched_district_code = self.find_min_distance(all_district_distances)
            if matched_district_code == None or not is_break:
                matched_district_name = ''
            else:
                matched_district_name = self.get_matched_district(matched_district_code)
            if is_break:
                break

        if matched_district_name:
            return matched_district_name, matched_district_code, input_sentence[:len(input_sentence) - len(sub_string)]
        else:
            return "", None, input_sentence
        
    def ward_pre(self, input_sentence, matched_district_code):
        input_sentence = remove_digital_string(input_sentence)
        # print("input_ward", input_sentence)
        matched_ward_name = None
        matched_ward_code = None
        is_break = False
        wards = self.get_wards(matched_district_code)
        for index in range(2, len(input_sentence), 1):
            sub_string = input_sentence[len(input_sentence) - index : len(input_sentence)]
            all_wards_distances = {}
            for ward in wards:
                data = ward['slug'].replace('-', '')
                if fuzz.token_sort_ratio(sub_string,data) > 80: # another number :))
                    is_break = True
                distance = self.levenshtein_distance(sub_string, data)
                all_wards_distances[ward['code']] = distance
            matched_ward_code = self.find_min_distance(all_wards_distances)
            if matched_ward_code == None or not is_break:
                matched_ward_name = ''
            else:
                matched_ward_name = self.get_matched_ward(matched_ward_code)
            if is_break:
                break

        if matched_ward_name:
            return matched_ward_name
        else:
            return ""
        
    def process(self, input_sentence):
        matched_provine_name,  matched_province_code, return_string = self.province_pre(input_sentence)
        matched_district_name,  matched_district_code, return_string  = self.district_pre(return_string, matched_province_code)
        matched_ward_name = self.ward_pre(return_string, matched_district_code)
        return {
            "province": matched_provine_name,
            "district": matched_district_name,
            "ward": matched_ward_name,
        }

    def test_case(self):
        start_time = time.time()*1000
        test_list = [
                    "TT Tân Bình Huyện Yên Sơn, Tuyên Quang",
                     "Nghi Sơ6n, T.X. Nghi Sơn, Thhanh Hóa",
                     "Nà Làng Phú Bình, Chiêm Hoá, Tuyên Quang",
                     "D2, Thạnh Lợi, Vĩnh Thạnh Cần Thơ",
                     "Đông Hòa,Tỉnh Phú yn",
                     "Phú Đô HuyệnPhú Lươnz"
                    ]
        for string in test_list:
            st = time.time()*1000
            print(self.process(string))
            et = time.time()*1000 - st
            print(" %s miliseconds " % et)
        end_time = (time.time()*1000 - start_time) / len(test_list)
        print("--- Average %s miliseconds per %d case ---" % (end_time, len(test_list)))

def validation(solution : Solution):
    TEAM_NAME = 'GTNC'
    EXCEL_FILE = f'result/{TEAM_NAME}.xlsx'
    data = load_json_test()
    summary_only = True
    df = []
    timer = []
    correct = 0

    for test_idx, data_point in enumerate(data):
        address = data_point["text"]
        ok = 0
        try:
            start = time.perf_counter_ns()
            result = solution.process(address)
            answer = data_point["result"]
            finish = time.perf_counter_ns()
            timer.append(finish - start)
            ok += int(answer["province"] == result["province"])
            ok += int(answer["district"] == result["district"])
            ok += int(answer["ward"] == result["ward"])
            df.append([
                test_idx,
                address,
                answer["province"],
                result["province"],
                int(answer["province"] == result["province"]),
                answer["district"],
                result["district"],
                int(answer["district"] == result["district"]),
                answer["ward"],
                result["ward"],
                int(answer["ward"] == result["ward"]),
                ok,
                timer[-1] / 1_000_000_000,
            ])
        except Exception as e:
            df.append([
                test_idx,
                address,
                answer["province"],
                "EXCEPTION",
                0,
                answer["district"],
                "EXCEPTION",
                0,
                answer["ward"],
                "EXCEPTION",
                0,
                0,
                0,
            ])
            # any failure count as a zero correct
            pass
        correct += ok

        if not summary_only:
            # responsive stuff
            print(f"Test {test_idx:5d}/{len(data):5d}")
            print(f"Correct: {ok}/3")
            print(f"Time Executed: {timer[-1] / 1_000_000_000:.4f}")
    print(f"-"*30)
    total = len(data) * 3
    score_scale_10 = round(correct / total * 10, 2)
    if len(timer) == 0:
        timer = [0]
    max_time_sec = round(max(timer) / 1_000_000_000, 4)
    avg_time_sec = round((sum(timer) / len(timer)) / 1_000_000_000, 4)

    df2 = pd.DataFrame(
        [[correct, total, score_scale_10, max_time_sec, avg_time_sec]],
        columns=['correct', 'total', 'score / 10', 'max_time_sec', 'avg_time_sec',],
    )
    columns = [
        'ID',
        'text',
        'province',
        'province_student',
        'province_correct',
        'district',
        'district_student',
        'district_correct',
        'ward',
        'ward_student',
        'ward_correct',
        'total_correct',
        'time_sec',
    ]

    df = pd.DataFrame(df)
    df.columns = columns
    print(f'{TEAM_NAME = }')
    print(f'{EXCEL_FILE = }')
    print(df2)

    writer = pd.ExcelWriter(EXCEL_FILE, engine='xlsxwriter')
    df2.to_excel(writer, index=False, sheet_name='summary')
    df.to_excel(writer, index=False, sheet_name='details')
    writer.close()

def clear_sub_string(string):
    remove_string = ["tỉnh", "thành phố", "quận", "huyện", "thị xã", "xã", "phường", "thị trấn", "t.", "tp.", "q.", "h.", "tx.", "x.", "p.", "tt.", "t.x", "t.t", "t.p"]
    string = string.lower()
    for rt in remove_string:
        if rt in string:
            string = string.replace(rt, "")
    string = remove_space_string(string)
    string = remove_comma_string(string)
    string = remove_dot_string(string)
    string = xoa_dau(string)
    return string

def remove_digital_string(string):
    return ''.join([i for i in string if not i.isdigit()])

def remove_comma_string(string):
    return string.replace(",", "")

def remove_dot_string(string):
    return string.replace(".", "")

def remove_space_string(string):
    return string.replace(" ", "")

def load_json_test():
    data = None
    with open('reference/public.json', encoding='utf8') as f:
        data = json.load(f)
    return data

def main():
    slo = Solution()
    slo.test_case()
    print("####################################")
    validation(slo)

if __name__ == '__main__':
    main()
