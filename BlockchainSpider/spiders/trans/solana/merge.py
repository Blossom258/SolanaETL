import pandas as pd
import os
def merge_csv_files(file1, file2, output_file):
    # 读取两个文件
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # 合并文件
    merged_df = pd.concat([df1, df2], ignore_index=True)

    # 写入到一个新的文件
    merged_df.to_csv(output_file, index=False)

if __name__=="__main__":

    # 指定文件路径
    file1 = r"D:\blockchainspider\BlockchainSpider\data\1_Transactions.csv"
    file2 = r"D:\blockchainspider\BlockchainSpider\data\2_Transactions.csv"
    output_file = r"D:\Blockchainspider\BlockchainSpider\data\Transactions.csv"
    merge_csv_files(file1, file2, output_file)
    print(f"Files merged into {output_file}")

    file3 = r"D:\blockchainspider\BlockchainSpider\data\1_Log.csv"
    file4 = r"D:\blockchainspider\BlockchainSpider\data\2_Log.csv"
    output_file = r"D:\Blockchainspider\BlockchainSpider\data\Log.csv"
    merge_csv_files(file3, file4, output_file)
    print(f"Files merged into {output_file}")

    file5 = r"D:\blockchainspider\BlockchainSpider\data\1_BalanceChanges.csv"
    file6 = r"D:\blockchainspider\BlockchainSpider\data\2_BalanceChanges.csv"
    output_file = r"D:\Blockchainspider\BlockchainSpider\data\BalanceChanges.csv"
    merge_csv_files(file5, file6, output_file)
    print(f"Files merged into {output_file}")
