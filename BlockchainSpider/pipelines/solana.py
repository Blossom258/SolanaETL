import json
import os
import csv
from collections import OrderedDict
from BlockchainSpider.items.solana import SignatureItem, TransactionsItem, AccountInfoItem, SolanaLogItem, \
    SolanaBalanceChangesItem, SolanaInstructionItem, SystemItem, SPLMemoItem, ValidateVotingItem, SPLTokenActionItem,\
    InnerInstructionItem,AddressItem,TokenAccountItem,BlockItem,SOLBalanceChangeItem,TokenBalanceChangeItem



class BasePipeline1:
    def __init__(self):
        self.file = None
        self.csv_writer = None
        self.headers_written = False  # 标记是否已经写入了表头

    def open_spider(self, spider):
        # 在爬虫启动时生成唯一的文件名，确保不会重复生成序号
        id = getattr(spider, 'id', 'default')  # 从 spider 中获取唯一的 id，默认为 'default'
        self.filename = f"{id}_{self.filename}"  # 设置文件名，生成文件一次
    def process_item(self, item, spider):
        # 设置输出路径并检查目录

        # 检查 item 类型是否符合预期
        if not isinstance(item, self.item_class):
            return item

        # 初始化 CSV 文件
        if self.file is None:
            fn = os.path.join(spider.out_dir, self.filename)  # 使用子类提供的文件名
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file)

        # 获取字段名（表头）
        item_dict = OrderedDict(item)  # 以确定字段顺序
        if not self.headers_written:
            self.csv_writer.writerow(item_dict.keys())  # 写入表头
            self.headers_written = True

        # 写入 item 数据
        self.csv_writer.writerow(item_dict.values())

        return item


    def close_spider(self, spider):
        # 关闭文件
        if self.file:
            self.file.close()

class BasePipeline:
    def __init__(self):
        self.file = None
        self.csv_writer = None
        self.headers_written = False  # 标记是否已经写入了表头

    def process_item(self, item, spider):
        # 如果没有指定输出目录，直接返回 item
        if spider.out_dir is None:
            return item

        # 检查 item 类型是否符合预期
        if not isinstance(item, self.item_class):
            return item

        # 初始化 CSV 文件
        if self.file is None:
            fn = os.path.join(spider.out_dir, self.filename)  # 使用子类提供的文件名
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file)

        # 获取字段名（表头）
        item_dict = OrderedDict(item)  # 以确定字段顺序
        if not self.headers_written:
            self.csv_writer.writerow(item_dict.keys())  # 写入表头
            self.headers_written = True

        # 写入 item 数据
        self.csv_writer.writerow(item_dict.values())

        return item


class SignaturePipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "signature.csv"  # 子类指定文件名
        self.item_class = SignatureItem  # 子类指定 item 类型


class AccountInfoPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "AccountInfo.csv"  # 子类指定文件名
        self.item_class = AccountInfoItem  # 子类指定 item 类型


class LogPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "Log.csv"  # 子类指定文件名
        self.item_class = SolanaLogItem  # 子类指定 item 类型


class BalanceChangePipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "BalanceChanges.csv"  # 子类指定文件名
        self.item_class = SolanaBalanceChangesItem  # 子类指定 item 类型


class SolanaInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "Instruction.csv"  # 子类指定文件名
        self.item_class = SolanaInstructionItem  # 子类指定 item 类型


class SystemInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "SystemInstruction.csv"  # 子类指定文件名
        self.item_class = SystemItem  # 子类指定 item 类型


class SPLMemoInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "SPLMemoInstruction.csv"  # 子类指定文件名
        self.item_class = SPLMemoItem  # 子类指定 item 类型


class ValidateVotingInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "ValidateVotingInstruction.csv"  # 子类指定文件名
        self.item_class = ValidateVotingItem  # 子类指定 item 类型


class SPLTokenInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "SPLTokenInstruction.csv"  # 子类指定文件名
        self.item_class = SPLTokenActionItem  # 子类指定 item 类型

class SPLTokenInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "SPLTokenInstruction.csv"  # 子类指定文件名
        self.item_class = SPLTokenActionItem  # 子类指定 item 类型

class InnerInstructionPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "InnerInstruction.csv"  # 子类指定文件名
        self.item_class = InnerInstructionItem  # 子类指定 item 类型

class RandomAddressesPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "RandomAddresses.csv"  # 子类指定文件名
        self.item_class = AddressItem  # 子类指定 item 类型

class TransactionsPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "Transactions.csv"  # 子类指定文件名
        self.item_class = TransactionsItem  # 子类指定 item 类型

class TokenAccountPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "TokenAccount.csv"  # 子类指定文件名
        self.item_class = TokenAccountItem  # 子类指定 item 类型

class BlockPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "Block.csv"  # 子类指定文件名
        self.item_class = BlockItem  # 子类指定 item 类型


class BlocktoSignaturePipeline:
    def __init__(self):
        self.file = None

    def process_item(self, item, spider):
        if spider.out_dir is None:
            return item
        if not isinstance(item, BlockItem):
            return item

        # init file from filename
        if self.file is None:
            fn = os.path.join(spider.out_dir, spider.name)
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'a')

        # write item
        json.dump({**item}, self.file)
        self.file.write('\n')
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()

# class SOLBalanceChangePipeline:
#     def __init__(self):
#         self.file = None
#         self.filename =  'solana.SOLBalanceChange'
#     def process_item(self, item, spider):
#         if spider.out_dir is None:
#             return item
#         if not isinstance(item, SOLBalanceChangeItem):
#             return item
#
#         # init file from filename
#         if self.file is None:
#             fn = os.path.join(spider.out_dir, self.filename)
#             if not os.path.exists(spider.out_dir):
#                 os.makedirs(spider.out_dir)
#             self.file = open(fn, 'a')
#
#         # write item
#         json.dump({**item}, self.file)
#         self.file.write('\n')
#         return item
#
#     def close_spider(self, spider):
#         if self.file is not None:
#             self.file.close()
#
# class TokenBalanceChangePipeline:
#     def __init__(self):
#         self.file = None
#         self.filename = 'solana.TokenBalanceChange'
#
#     def process_item(self, item, spider):
#         if spider.out_dir is None:
#             return item
#         if not isinstance(item, TokenBalanceChangeItem):
#             return item
#
#         # init file from filename
#         if self.file is None:
#             fn = os.path.join(spider.out_dir, self.filename)
#             if not os.path.exists(spider.out_dir):
#                 os.makedirs(spider.out_dir)
#             self.file = open(fn, 'a')
#
#         # write item
#         json.dump({**item}, self.file)
#         self.file.write('\n')
#         return item
#
#     def close_spider(self, spider):
#         if self.file is not None:
#             self.file.close()

class SOLBalanceChangePipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "SOLBalanceChange.csv"  # 子类指定文件名
        self.item_class = SOLBalanceChangeItem  # 子类指定 item 类型

class TokenBalanceChangePipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.filename = "TokenBalanceChange.csv"  # 子类指定文件名
        self.item_class = TokenBalanceChangeItem  # 子类指定 item 类型

