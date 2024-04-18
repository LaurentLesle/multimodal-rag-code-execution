# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from promptflow import tool
import sys
import os; print(os.getcwd())
sys.path.append("../../code")
from doc_utils import search

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need


@tool
def search_index_one(query: str, index_one: str) -> str:
    return search(query, index_name=index_one, computation_approach="NoComputationTextOnly")
