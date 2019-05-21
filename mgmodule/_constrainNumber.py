def constrainNumber(n, minn, maxn):
	""" Constraining number to lie between minn and maxn """
	return max(min(maxn, n), minn)
