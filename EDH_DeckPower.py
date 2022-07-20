#!/usr/bin/env python
# coding: utf-8

# In[2]:


#統率者戦(EDH)用、デッキパワー診断アプリ

import csv
import math

import time

#スクレイピング用ライブラリ
from bs4 import BeautifulSoup
from urllib.request import urlopen

#グラフ描画用ライブラリ
import numpy as np
import matplotlib.pyplot as plt

#----------------------------------------------------------------------------------------------
#実装方針
#デッキリストを記した、マジックオンライン用のテキストファイルを一行目から順次読み込む
#Wisdom Guildで該当カードのタイプ、マナコスト、平均価格をスクレイピングして、記録する。

#カードタイプ、マナ点数ごとの枚数、構築費用総額を算出し、マナカーブを棒グラフで表示する

#ゆくゆくは、統率者のカードパワー、構築費用などの傾向から、
#既存のデッキリスト（構築済EDHデッキや、大会入賞デッキ）を教師データとして学習を行い、概算デッキレベルを算出する。
#----------------------------------------------------------------------------------------------

#Wisdom Guildからカード情報をスクレイピングするための関数 cardScraiping()  英語版でのカード名を引数とする
def cardScraiping(cardName):
    
    '''
    カード名をURLに埋め込んで、Wisdom Guildのカード個別ページにアクセスするために、
    カード名の" "(半角スペース)を"+"、"," (カンマ)を"%2C"、"'"(アポストロフィー)を"%27"にそれぞれ置換する。
    
    この他にも置換が必要な文字列があれば、都度、追加していく
    例：《リム＝ドゥールの櫃/Lim-Dûl's Vault》の特殊文字"û"など
    '''
    
    var = cardName
    
    #変数 length を宣言。これはカード名の文字数（スペースや特殊記号含む）
    length = len(cardName)
    
    #URLに埋め込むためのカード名 convertedCardName を宣言
    convertedCardName = ""
    
    #先頭の文字から順番に（必要に応じて内容を置換しながら）文字列を連結する。xは文字を格納するための変数
    for i in range(length):
        x = cardName[i]
        
        if(x == " "):
            x = "+"
            
        #カンマは、固有名詞を伴う伝説のカード名を中心に、広く存在
        elif(x == ","):
            x = "%2C"
            
        #アポストロフィーは、所有格(～の)を伴うカード名に、広く存在
        elif(x == "'"):
            x = "%27"
            
        #《リム＝ドゥールの櫃/Lim-Dûl's Vault》の"û"(アクサン・シルコンフレックス付きのu)を、普通の"u"に置換する
        elif(x == "û"):
            x = "u"
        
        #文字列に順次連結
        convertedCardName = convertedCardName + x
        
    '''
    Wisdom Guildにおける、個別カードのURL命名規則は、「"http://whisper.wisdom-guild.net/card/" + convertedCardName +"/"」である。
    例えば、《自然の怒りのタイタン、ウーロ/Uro, Titan of Nature's Wrath》の場合、
    URLは、"http://whisper.wisdom-guild.net/card/Uro%2C+Titan+of+Nature%27s+Wrath/"　となる。
    '''
        
    prehtml = "http://whisper.wisdom-guild.net/card/"
    html = urlopen(prehtml + convertedCardName + "/")
    
    data = html.read()
    html = data.decode('utf-8')
    
    
    # time.sleep(x)で、x秒待機
    time.sleep(3)
    # HTMLを解析
    soup = BeautifulSoup(html, 'html.parser')
    
    '''
    ★マナコストの値を含むHTML部分を抽出する
    ここで、マナコスト（manaCost）は、「<td class="lc">(３)(青)(青)</td>」のような形で出力されるので、
    前後のタグ部分をスライスして切除する
    '''
    
    preManaCost = soup.find_all("td", class_="lc")
    manaCost = str(preManaCost[0])

    manaCost = manaCost[15:-5]
    
    '''
    ★カードタイプの値を含むHTML部分を元に、カードタイプを判断する
    ここで、カードタイプのHTMLは、
    「<td class="mc"><a href="http://whisper.wisdom-guild.net/search.php?cardtype[]=Creature">
    クリーチャー</a> — <a href="http://whisper.wisdom-guild.net/search.php?subtype[]=Devil">デビル(Devil)</a> </td>」
    のような、長い文字列で出てくるので、各種カードタイプを示す文言が、文字列内に登場するかどうかをif文で判断する
    '''
    
    #クラス名が"mc"のhtmlを取得する
    #なお、Wisdom Guildの個別カードページで、カードタイプは、
    #日本語版が存在するカードであれば、preCardType[1]に、日本語版が存在しない昔のカードであれば、preCardType[2]に入っている
    preCardType = soup.find_all("td", class_="mc")
    cardType = str(preCardType[1]) + str(preCardType[2])
    
    #カードタイプが伝説かどうかを判断する。文字列 Legend（初期値は""）を宣言し、HTML中に”伝説の”という文言を含むなら、その旨を追加する
    Legend = ""
    if(('伝説の' in cardType) is True):
        Legend = "伝説の"
    
    #cardTypeに"クリーチャー"という文字列を含んでいれば、cardTypeを"クリーチャー"に更新する。
    #以下、インスタント、ソーサリー、アーティファクト、エンチャント、プレインズウォーカー、土地についても同様の処理を行う。
    if(('クリーチャー' in cardType) is True):
        cardType = "クリーチャー"
    elif(('インスタント' in cardType) is True):
        cardType = "インスタント"
    elif(('ソーサリー' in cardType) is True):
        cardType = "ソーサリー"
    elif(('アーティファクト' in cardType) is True):
        cardType = "アーティファクト"
    elif(('エンチャント' in cardType) is True):
        cardType = "エンチャント"
    elif(('プレインズウォーカー' in cardType) is True):
        cardType = "プレインズウォーカー"
    elif(('土地' in cardType) is True):
        cardType = "土地"
    
    #伝説であれば、カードタイプの先頭に”伝説の”と追加される
    cardType = Legend + cardType
    
    
    '''
    ★カードの値段（平均値）を含むHTML部分を元に、カードの値段を判断する
    ここで、カード値段のHTMLは、
    「<div class="contents"><big>最安：<b>199</b> 円</big>／トリム平均：<b>344</b> 円<div class="right">
    （参考：<b>80</b>～<b>500</b> 円）有効データ数：11 件</div> </div>」のような文字列で出てくる。
    
    平均値の金額のみを取り出すべく、文字列の先頭から内容を走査し、
    「トリム平均」の"ト"の字が見つかったら、その時点から順に文字列に追加し、"円"の字が出たら、ループを離脱する
    '''
    preCardPrice = soup.find_all("div", class_="contents")
    cardPrice = str(preCardPrice[1])
    
    #カードの値段の平均値を格納する変数 cardPriceAverage を宣言
    cardPriceAverage = ""
    #「トリム平均」の"ト"の文字が見つかったかどうかを判断するフラグ変数 flag
    flag = False
    for i in range(len(cardPrice)):
        var = cardPrice[i]
        if((var == "ト") or (flag == True)):
            flag = True
            cardPriceAverage = cardPriceAverage + var
            if(var == "円"):
                break
    """
    この時点での cardPriceAverage は「トリム平均：<b>867</b> 円」という形で出てくるので、
    bタグ以前、以後をスライスして切除する。
    """
    cardPriceAverage = cardPriceAverage[9:-6]
          
    #区切り文字は"&"を使用　（スペースやコロンだと、後々.split()でリストに変換する際、カード名と混同するため）
    result = manaCost + "&" + cardType + "&" + cardPriceAverage
    
    return result


#「(２)(青)(赤)」のようなカッコ書きマナコストを、点数で見たマナコスト（整数型）に変換する関数
def calcConvertedManaValue(manaSymbol):
    processingManaValue = manaSymbol
    
    #最終的な返り値 convertedManaValue を宣言（初期値０）
    convertedManaValue = 0   
    
    #マナコストに(X)が含まれていれば除去する　※ルール上、不特定マナ部分は０マナ扱い
    if(('(Ｘ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(Ｘ)', '')
        
    #マナコストに(0)が含まれていれば無視するために、除去する
    if(('(０)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(０)', '')
        
    #マナコストに氷雪マナ(氷)が含まれていれば、"S"に置換する。Sは氷雪マナを表す
    if(('(氷)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(氷)', 'S')
        
    #マナコストに無色マナ(◇)が含まれていれば、"N"に置換する。Nは無色マナを表す
    if(('(◇)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(◇)', 'N')
        
    #マナコストにファイレクシアマナシンボル（例：(黒/Φ)）を含んでいれば、その色のマナ１点に置換する。
    if(('(白/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(白/Φ)', 'W')
    if(('(青/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(青/Φ)', 'U')
    if(('(黒/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(黒/Φ)', 'B')
    if(('(赤/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(赤/Φ)', 'R')
    if(('(緑/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(緑/Φ)', 'G')
        
        
    """
    #マナコストに、混成ファイレクシアマナシンボルを含んでいれば、M(混成マナ１点)に置換する。
    
    ※2022/6時点で、《完成化した賢者、タミヨウ/Tamiyo, Compleated Sage》専用であり、
    Wisdom Guildでも表記が定まっていないので、保留
    
    if(('(緑/青/Φ)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(緑/青/Φ)', 'M')
    
    """
        
    #マナコストに単色混成マナシンボル（例：(２/白)）を含んでいれば、"NN"に置換する。（Nは無色マナ、NNはそれが２点であることを示す）
    # ※単色混成マナシンボルはルール上、大きいほうのマナコスト、すなわち無色２点分とみなす
    #各色に対して判定を行う
    if(('(２/白)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(２/白)', 'NN')
    if(('(２/青)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(２/青)', 'NN')
    if(('(２/黒)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(２/黒)', 'NN')
    if(('(２/赤)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(２/赤)', 'NN')
    if(('(２/緑)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(２/緑)', 'NN')
        
    #マナコストに混成マナ(/ スラッシュを含んでいるかで判断)が含まれていれば、"M"に置換する。Mは混成マナを表す
    if(('/' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(赤/緑)', 'M')
        processingManaValue = processingManaValue.replace('(白/黒)', 'M')
        processingManaValue = processingManaValue.replace('(白/青)', 'M')
        processingManaValue = processingManaValue.replace('(緑/白)', 'M')
        processingManaValue = processingManaValue.replace('(赤/白)', 'M')
        processingManaValue = processingManaValue.replace('(青/赤)', 'M')
        processingManaValue = processingManaValue.replace('(黒/赤)', 'M')
        processingManaValue = processingManaValue.replace('(緑/青)', 'M')
        processingManaValue = processingManaValue.replace('(黒/緑)', 'M')
        processingManaValue = processingManaValue.replace('(青/黒)', 'M')
                
        
    #マナコストに(白)が含まれていれば、"W"に置換する
    if(('(白)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(白)', 'W')
        
    #マナコストに(青)が含まれていれば、"U"に置換する
    if(('(青)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(青)', 'U')
        
    #マナコストに(黒)が含まれていれば、"B"に置換する
    if(('(黒)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(黒)', 'B')
        
    #マナコストに(赤)が含まれていれば、"R"に置換する
    if(('(赤)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(赤)', 'R')
        
    #マナコストに(緑)が含まれていれば、"G"に置換する
    if(('(緑)' in processingManaValue) is True):
        processingManaValue = processingManaValue.replace('(緑)', 'G')
        
    """
    ここまでの処理を行った結果、processingManaValueの内容は「UR」のような色マナだけの状態か、
    (１)U、(１０)RRのように、（無色マナの数）+色マナ、あるいは(２)のように無色マナのみの形式になっている。
    (０)、(Ｘ)は、すでに取り除かれている。
    
    次の処理として、もしprocessingManaValueの先頭が"("であれば、１点以上の無色マナが入っているので、
    （無色マナの数）の部分を、その数に等しいNに置換する
        
    """
    
    #文字列に換算したマナコストを格納する変数 literalManaValue を宣言
    literalManaValue = ""
    
    #processingManaValue の先頭が何かしらの色マナである場合
    if((processingManaValue != "") and (processingManaValue[0] != ("("))):
        literalManaValue += processingManaValue
    
    
    #無色マナの数が１桁の場合    
    elif((processingManaValue != "") and (processingManaValue[0] == "(") and (processingManaValue[2] == ")")):
        #カッコの中身の整数を繰返し回数として設定
        x = int(processingManaValue[1])
        
        for i in range(x):
            processingManaValue = processingManaValue + "N"
        
            #この時点で、マナコスト(３)(黒)(緑)の文字列であれば、「（3）BGNNN」のような文字列になっている
            #冒頭にカッコ部分を含むなら、スライスして切除
            if(('(' in processingManaValue) is True):
                literalManaValue = processingManaValue[3:]

    #無色マナの数が２桁の場合              
    elif((processingManaValue != "") and (processingManaValue[0] == "(") and (processingManaValue[3] == ")")):
        #カッコの中身の整数を繰返し回数として設定
        x = int(processingManaValue[1] + processingManaValue[2])
        
        for i in range(x):
            processingManaValue = processingManaValue + "N"
        
            #この時点で、マナコスト(１０)(赤)(赤)の文字列であれば、「（１０）RRNNNNNNNNNN」のような文字列になっている
            #冒頭にカッコ部分を含むなら、スライスして切除
            if(('(' in processingManaValue) is True):
                literalManaValue = processingManaValue[4:]

    
    #文字列 literalManaValueの文字数を、マナ総量 convertedManaValueとして記録する
    convertedManaValue += len(literalManaValue)
    
    #デバッグ用
    #print("processingManaValue:" + processingManaValue)
    #print("literalManaValue:" + literalManaValue)
    
    
    return convertedManaValue


#読み込んだテキストファイルの各行を一時格納するためのリスト deckList
deckList = list()

#読み込んだテキストファイルの各行を、逐次追加するためのリスト globalDeckList
globalDeckList = list()

#デッキリストを記載したファイル「deck-list.txt」を読み込む
with open("deck-list.txt", "r", encoding="utf-8") as f:
    reader = f.readlines()
    for row in (reader):
        #print(row)
        deckList.append(row)
        
    #デッキリストの各行をリストに格納
    #print(deckList)
    
    #カード種類総数
    kindOfCards = len(deckList)

#----------統計に用いる各種情報を変数として定義-------------------------
#統率者の名前
nameOfCommander = ""

#統率者の固有色
colorOfCommander = ""

#統率者のカード金額
priceOfCommander = ""

#レジェンドカードの枚数
numberOfLegend = 0

#土地カードの枚数
numberOfLand = 0

#デッキのカード総額
totalPriceOfDecks = 0

#カード情報を二次元配列で管理するためのリスト
twoDimensionalDeckList = list()

#デッキのカード金額の序列を格納するためのリスト(後から降順に整列する)
#カード金額の中央値や、上位数%の金額を取得するために作成
cardPriceRanking = list()

"""
#点数で見たマナコストの枚数ごとの分布を記録するリスト manaCostDistributionを宣言。
#要素数は、17個（0～16マナ）とする。これは、2022年時点で、《ドラコ/Draco》の16マナが最大のため。 
#※銀枠の《グリーマックス/Gleemax》(1000000マナ)は考慮しない。
#不特定マナ(X)部分は0マナとして扱う。また、待機持ちなど、マナコストを持たない呪文は０マナとして扱う。
#このリストに土地はカウントしない
"""
manaCostDistribution = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

#----------統計量ここまで------------------------------------------------
    
for i in range(kindOfCards):
    var = deckList[i]
    #この時点でのvarの中身は「1 カード名」（採用枚数、半角スペース、英語版カード名）

    
    #採用枚数とカード名を取り出す
    #採用枚数が一桁（=２文字目が空白スペース）の場合は、先頭2文字を切除した内容をカード名として記録、先頭1文字をカード枚数として記録
    if(var[1] == " "):
        varCardName = var[2:]
        varCardNumber = var[:1]
    else:
        #そうでない場合は採用枚数が二桁なので、先頭3文字を切除した内容をカード名として記録、先頭2文字をカード枚数として記録
        varCardName = var[3:]
        varCardNumber = var[:2]    
    
    #読み込んだ行がリスト末尾である場合はそのまま何もせず、それ以外であれば、行末の改行"\n"を切除
    if(i == kindOfCards-1):
        #特に何もしない（何か書かないと構文エラーになるので便宜上記述）
        varCardName = varCardName[:]
    else:
        #リスト末尾以外であれば、[:-1]でスライスし、要素末尾の\nを削除
        varCardName = varCardName[:-1]
        
    #ここで、varCardNameを引数として、WisdomGuildからカードタイプ、マナコスト、平均価格を
    #スクレイピングしてくる関数 cardScraiping()を呼び出す
    #スクレイピングしてきた各種情報は変数 cardInfoに格納
    cardInfo = cardScraiping(varCardName)
    
    #区切り文字は"&"を使用、理由は先述
    cardInformationList = varCardNumber + "&" + varCardName + "&" + cardInfo
    
    #内容確認のために、採用枚数、カード名、マナコスト、カードタイプ、平均価格をリスト形式で出力する
    print(cardInformationList.split("&"))
    
    #カード情報を都度、二次元配列に追加
    twoDimensionalDeckList.append(cardInformationList.split("&"))
    
    
        
    #文字列 cardInfoから、点数で見たマナコストのみを取り出す。
    #なお、この時点でのcardInfoの中身は「(２)(青)(赤)&伝説のクリーチャー&192」のような&区切りの文字列になっている。
    
    #まず、前段階として、文字列cardInfoから、カッコ表記のマナコストのみを取り出す
    manaSymbolValue = str("")
    for i in range(len(cardInfo)):
        var = cardInfo[i]
        if(var == "&"):
            break
            
        manaSymbolValue = manaSymbolValue + var
    
    
    #カッコ表記のマナコスト manaSymbolValueを、点数で見たマナコストに変換する関数 calcconvertedManaValue() ,引数は「(２)(青)(赤)」のような文字列
    manaValue = calcConvertedManaValue(manaSymbolValue)
    
    
    
    #文字列 cardInfoから、カードタイプのみを取り出す。
    #なお、この時点でのcardInfoの中身は「(２)(青)(赤)&伝説のクリーチャー&192」のような&区切りの文字列になっている。
    #先頭の文字から走査し、&が出るまでスライス、その後、末尾の文字列からも同様の処理を行う
    
    """
    必要に応じて後で記述
    """



    #文字列 cardInfoから、平均価格のみを取り出す。
    #なお、この時点でのcardInfoの中身は「(２)(青)(赤)&伝説のクリーチャー&192」のような&区切りの文字列になっている。
    #それぞれ、マナコスト、カードタイプ、平均価格を表す
    
    intCardPrice = str("")
    
    #カード名の通し番号
    serialNumber = 1
    
    for i in range(len(cardInfo)):
        var = cardInfo[-i-1]
        if(var == "&"):
            break
            
        intCardPrice = var + intCardPrice
        
    
    #文字列型だった数値を整数型に変換。その際に、桁区切りのカンマはreplaceで削除
    intCardPrice = int(intCardPrice.replace(',', ''))
    
    #カード価格を、ランキング用リストに追加
    cardPriceRanking.append(intCardPrice)
    
    
    #デバッグ用
#     print(varCardName)#カード名
#     print(intCardPrice)#カードの平均価格（整数型）
#     print(manaSymbolValue)#カードのマナシンボル
#     print(manaValue)#カードの、点数で見たマナコスト


    #レジェンドカードであればインクリメント
    if(('伝説の' in cardInformationList) is True):
        numberOfLegend += 1
        


    #デッキ内のカード総額をインクリメント
    number = int(varCardNumber)
    price = intCardPrice
    totalPriceOfDecks += (number * price)
    
    #累計金額
    #print("累計金額：" + str(totalPriceOfDecks) + "円")
    
    
    #土地カードであればインクリメント
    if(('土地' in cardInformationList) is True):
        numberOfLand += number
    
    #通し番号をインクリメント
    serialNumber += 1
    
    
    #マナ総量を、マナ総量分布を表すリスト manaCostDistribution に追加
    #マナ総量が０マナでなおかつ土地でない場合は、０マナの呪文としてカウント
    #土地はここではカウントせず、変数 numberOfLand で別途カウント
    
    #デバッグ用
    #print("cardInfo:" + cardInfo)
    #土地カードであるかどうか
    #print("土地" in cardInfo)
    
    #土地カードでない場合、点数で見たマナコストを、マナコスト分布を示すリスト manaCostDistribution の適切な箇所にインクリメント
    if(("土地" in cardInfo) is False):
        manaCostDistribution[manaValue] += 1
    
    #マナ総量分布リスト（確認用）
    #print(manaCostDistribution)
    

    #その後、記録用のcsvファイルに、一行ずつ結果を書き出していく

nameOfCommander = twoDimensionalDeckList[0][1]
priceOfCommander = twoDimensionalDeckList[0][4]

print()#改行
print("統率者：" + nameOfCommander)
print("統率者の平均金額(円)：" + priceOfCommander)
print("レジェンドの枚数：" + str(numberOfLegend) + "/100")
print("土地の枚数：" + str(numberOfLand) + "/100")

print("デッキ費用総額(円)：" + str(totalPriceOfDecks))

print("マナ総量分布")
print(manaCostDistribution)


print("カード金額ランキング内訳")
list.sort(cardPriceRanking, reverse=True)
print(cardPriceRanking)

print("最高金額(円)：" + str(cardPriceRanking[0]))

#トップ３の平均金額
topThreePriceAverage = np.mean(cardPriceRanking[0:3])
print("トップ３平均金額(円)：" + str(topThreePriceAverage))

#トップ10の平均金額
topTenPriceAverage = np.mean(cardPriceRanking[0:10])
print("トップ10平均金額(円)：" + str(topTenPriceAverage))

#トップ25の平均金額
topTwentyFivePriceAverage = np.mean(cardPriceRanking[0:25])
print("トップ25平均金額(円)：" + str(topTwentyFivePriceAverage))

#トップ50の平均金額
topFiftyPriceAverage = np.mean(cardPriceRanking[0:50])
print("トップ50平均金額(円)：" + str(topFiftyPriceAverage))

# """
# パラメータとして使えそうな値
# ・統率者の平均金額
# ・デッキ総額
# ・トップ２５の平均金額
# （トップ１０までの平均だと、５色のデュアルランド全部入りデッキなんかは必然的に高額になる傾向が出る）

# """


#マナコストの棒グラフ
"""
#グラフの内容を変更するには、リスト manaCurveの内容を変更
"""
manaCurve = manaCostDistribution

left = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])

#刻み幅を設定
plt.xticks([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])

#描画するデータセット
height = np.array(manaCurve)

#ラベルを中央にセット
plt.bar(left, height, align="center")

#グリッドを描画
plt.grid(color = "gray", linestyle="--")

# 軸ラベルの設定
plt.xlabel("Converted Mana-Cost")
plt.ylabel("Number of Cards")


# In[ ]:




