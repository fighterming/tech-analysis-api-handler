from tech_analysis_api_v2.api import *
from tech_analysis_api_v2.model import *
import threading
import sys

event = threading.Event()


def OnDigitalSSOEvent(aIsOK, aMsg):
    print(f"OnDigitalSSOEvent: {aIsOK} {aMsg}")


def OnTAConnStuEvent(aIsOK):
    print(f"OnTAConnStuEvent: {aIsOK}")
    if aIsOK:
        event.set()


def OnUpdate(ta_Type: eTA_Type, aResultPre, aResultLast):

    if aResultPre != None:
        if ta_Type == eTA_Type.SMA:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.EMA:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.WMA:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.SAR:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.RSI:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.MACD:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.KD:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.CDP:
            print(f"前K {str(aResultPre)}")
        if ta_Type == eTA_Type.BBands:
            print(f"前K {str(aResultPre)}")
    if aResultLast != None:
        if ta_Type == eTA_Type.SMA:
            print(f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, SMA:{aResultLast.Value}")
        if ta_Type == eTA_Type.EMA:
            print(f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, EMA:{aResultLast.Value}")
        if ta_Type == eTA_Type.WMA:
            print(f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, EMA:{aResultLast.Value}")
        if ta_Type == eTA_Type.SAR:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, SAR:{aResultLast.SAR}, EPh:{aResultLast.EPh}, EPl:{aResultLast.EPl}, AF:{aResultLast.AF}, RaiseFall:{aResultLast.RaiseFall}"
            )
        if ta_Type == eTA_Type.RSI:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, RSI:{aResultLast.RSI}, UpDn:{aResultLast.UpDn}, UpAvg:{aResultLast.UpAvg}, DnAvg:{aResultLast.DnAvg}"
            )
        if ta_Type == eTA_Type.MACD:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, DIF:{aResultLast.DIF}, OSC:{aResultLast.OSC}"
            )
        if ta_Type == eTA_Type.KD:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, K:{aResultLast.K}, D:{aResultLast.D}"
            )
        if ta_Type == eTA_Type.CDP:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, CDP:{aResultLast.CDP}, AH:{aResultLast.AH}, NH:{aResultLast.NH}, AL:{aResultLast.AL}, NL:{aResultLast.NL}"
            )
        if ta_Type == eTA_Type.BBands:
            print(
                f"最新 Time:{aResultLast.KBar.TimeSn_Dply}, MA:{aResultLast.MA}, UB2:{aResultLast.UB2}, LB2:{aResultLast.LB2}"
            )


def OnRcvDone(ta_Type: eTA_Type, aResult):
    if ta_Type == eTA_Type.SMA:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.EMA:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.WMA:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.SAR:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.RSI:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.MACD:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.KD:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.CDP:
        for x in aResult:
            print(f"回補 {x}")
    if ta_Type == eTA_Type.BBands:
        for x in aResult:
            print(f"回補 {x}")


def option():
    ProdID = input("商品代號: ")
    SNK = input("分K(1/3/5): ")
    STA_Type = input("指標(SMA/EMA/WMA/SAR/RSI/MACD/KD/CDP/BBands): ")
    DateBegin = input("日期(ex: 20230619): ")

    NK = eNK_Kind.K_1m
    if SNK == "1":
        NK = eNK_Kind.K_1m
    elif SNK == "3":
        NK = eNK_Kind.K_3m
    elif SNK == "5":
        NK = eNK_Kind.K_5m

    TA_Type = eTA_Type.SMA
    if STA_Type == "SMA":
        TA_Type = eTA_Type.SMA
    elif STA_Type == "EMA":
        TA_Type = eTA_Type.EMA
    elif STA_Type == "WMA":
        TA_Type = eTA_Type.WMA
    elif STA_Type == "SAR":
        TA_Type = eTA_Type.SAR
    elif STA_Type == "RSI":
        TA_Type = eTA_Type.RSI
    elif STA_Type == "MACD":
        TA_Type = eTA_Type.MACD
    elif STA_Type == "KD":
        TA_Type = eTA_Type.KD
    elif STA_Type == "CDP":
        TA_Type = eTA_Type.CDP
    elif STA_Type == "BBands":
        TA_Type = eTA_Type.BBands

    return TechAnalysis.get_k_setting(ProdID, TA_Type, NK, DateBegin)


def main():
    if len(sys.argv) < 3:
        print("python example.py 帳號 密碼")
        sys.exit()

    ta = TechAnalysis(OnDigitalSSOEvent, OnTAConnStuEvent, OnUpdate, OnRcvDone)
    ta.Login(sys.argv[1], sys.argv[2])
    event.wait()

    opt = input("1: 指標\n2: 歷史成交\n> ")
    if opt == "1":
        k_config = option()
        ta.SubTA(k_config)
        input("running...\n")
        ta.UnSubTA(k_config)

    elif opt == "2":
        lsBS, sErrMsg = ta.GetHisBS_Stock("2330", "20240506")
        for x in lsBS:
            msg = (
                f"代號: {x.Prod=}, 成交時間: {x.Match_Time}, "
                + f"成交價格: {x.Match_Price}, 成交數量: {x.Match_Quantity}, "
                + f"試搓: {x.Is_TryMatch}, 買賣: {x.BS}"
            )

            print(msg)

    input("end.\n")


main()
