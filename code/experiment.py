import argparse
import workflow
import os
import pandas as pd
"""
主程式
"""
if __name__ == "__main__":
   
    text_prog="""Automation C++-based Malware Generation by Large language model."""
    text_usage=""""""
    text_description="""THIS WORK IS FROM ANTSLAB(EE603-2) FROM NTUST"""
    text_epilog=""""""
    parser=argparse.ArgumentParser(prog=text_prog,usage=text_usage,description=text_description,epilog=text_epilog)

    parser.add_argument("-Tt","--tactic",required=False ,type=str,dest="ID",help="The workflow will generate at least one instance of every technique in specific tactic;the number can be later set by \"number\". ")
    parser.add_argument("-t","--technique",required=False,type=str,dest="ID",help="The workflow will generate at least one instance of the specific technique.the number can be later set by \"number\".")
    parser.add_argument("-s","--software",required=False,type=str,dest="ID")
    parser.add_argument("-g,""--group",required=False,type=str,dest="ID")
    parser.add_argument("-c","--campaign",required=False,type=str,dest="ID")
    #parser.add_argument("-n","--number",default=1,required=False ,help="The number of the instances will be generated.")
    #parser.add_argument("-d","--document",default=None,type=str,dest="ID",required=False,help="Generate instances based on the (.xlsx)document.")
    #parser.add_argument("--sigmarule",default=None,dest="modeGeneration",type=str,required=False)
    """
    operation
    """
    parser.add_argument("-d","--detail",default="",required=False,type=str,dest="detail")
    parser.add_argument("--operation",default=1,type=int,required=False,dest="operation")
    args = parser.parse_args()

    """
    下方為主要功能

    """
    if parser.parse_args().ID==None:ID="N"
    ID=parser.parse_args().ID
    if parser.parse_args().operation <4 :
        """GENERATION"""
        dictInput=workflow.dataLookUp(ID=ID) 
        detail=parser.parse_args().detail
        dictInput['inputType']="t2m"           
        dictInput['detail']=detail          
        workflow.workflow(dictInput=dictInput,operation=parser.parse_args().operation)
    else :
        """LOOKUP"""
        print(workflow.dataLookUp(ID=ID))
        """這邊應該要印出該ID的事項"""


"""
這個.py的用途是拿來用cmd跑指令跟試著寫一個cui
"""