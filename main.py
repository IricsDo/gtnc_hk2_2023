import xlrd
import download_data
import pandas as pd
from os import devnull


def pre_process_data():
    if download_data.check_data_exists():
        print('[@@@@@@] Data already exist !')
    else:
        print('[@@@@@@] Pull data from url ...')
        if download_data.pull_data():
            print('[@@@@@@] Download finished')
        else:
            print('[@@@@@@] Have some problem with data, exit program !!')
            exit(-1)
    
    wb = xlrd.open_workbook('data/data.xls', logfile=open(devnull, 'w'))
    df = pd.read_excel(wb, dtype=str, engine='xlrd')
    #print(df.head())
    
    
    data = df[["Tỉnh Thành Phố","Quận Huyện", "Phường Xã"]]
    print(data)
            
def inference():
    pass

    
def post_process_result():
    pass


def main():
    pre_process_data()
    inference()
    post_process_result()
    
    
if __name__ == '__main__':
    main()