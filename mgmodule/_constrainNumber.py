def constrainNumber(n, minn, maxn):
    """
    Constraining number to lie between minn and maxn
    
    Parameters:
    - n (number)
    - minn (lower limit n can be)
    - maxn (lower limit n can be)
    
    return:
    Constrained number
    """
    return max(min(maxn, n), minn)
