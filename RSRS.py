import pandas as pd
import os
import datetime
import numpy as np
import statsmodels.formula.api as sml
import matplotlib.pyplot as plt
import scipy.stats as scs
import matplotlib.mlab as mlab

data=pd.read_csv("btc20200201__20200301.csv",usecols=['open_time','open','high','low','close','volume'])
# print(data)
N=18
M=600
L=8
data['beta']=0
data['R2']=0
data['MA']=data['close'].rolling(L).mean()
for i in range(1, len(data) - 1):
    df_ne = data.loc[i - N + 1:i, :]
    model = sml.ols(formula='high~low', data=df_ne)
    result = model.fit()

    data.loc[i + 1, 'beta'] = result.params[1]
    data.loc[i + 1, 'R2'] = result.rsquared

# for j in range(1,len((data)-1)):
#     df_ne = data.loc[j-L+1,:]


data['return']=data.close.pct_change(1)
data['beta_norm'] = (data['beta'] - data.beta.rolling(M).mean().shift(1)) / data.beta.rolling(M).std().shift(1)
for i in range(M):
    data.loc[i, 'beta_norm'] = (data.loc[i, 'beta'] - data.loc[:i - 1, 'beta'].mean()) / data.loc[:i - 1,'beta'].std()
data.loc[2, 'beta_norm'] = 0
data['RSRS_R2'] = data.beta_norm * data.R2
data = data.fillna(0)

# 右偏标准分
data['beta_right'] = data.RSRS_R2 * data.beta
# print(data)

data=data.iloc[7:]
data =data.reset_index(drop = True)
# data.to_csv('ceshi.csv')
# print(data)


# #画出斜率数据分析图
# plt.figure(figsize=(15,5))
# plt.hist(data['beta'], bins= 100, range= None, weights= None, cumulative= False,
#          bottom= None, histtype= 'bar', align= 'mid', orientation= 'vertical', rwidth= None, log= False, color= 'r',
#          label='斜率分布', stacked= False)
# plt.show()
#
# #RSRS标准分和右偏变准分分布
# plt.figure(figsize=(15,5))
# plt.hist(data['beta_norm'], bins= 100, range= None, weights= None, cumulative= False,
#          bottom= None, histtype= 'bar', align= 'mid', orientation= 'vertical', rwidth= None, log= False, color= 'r',
#          label='标准分分布', stacked= False)
# plt.show()
#
# plt.figure(figsize=(15,5))
# plt.hist(data['RSRS_R2'], bins= 100, range= None, weights= None, cumulative= False,
#          bottom= None, histtype= 'bar', align= 'mid', orientation= 'vertical', rwidth= None, log= False, color= 'r',
#          label='右偏标准分分布', stacked= False)
# plt.show()

sta = scs.describe(data.beta)
stew = sta[4]
kurtosis = sta[5]

sta1 = scs.describe(data.beta_norm)
stew1 = sta1[4]
kurtosis1 = sta1[5]

sta2 = scs.describe(data.RSRS_R2)
stew2 = sta2[4]
kurtosis2 = sta2[5]

print('斜率的均值:%s' % (data['beta'].mean()))
print('斜率的标准差:%s' % (data['beta'].std()))
print('斜率的偏度:%s' % (stew))
print('斜率的峰度:%s' % (kurtosis))
print('')
print('斜率标准分的均值:%s' % (data['beta_norm'].mean()))
print('斜率标准分的标准差:%s' % (data['beta_norm'].std()))
print('斜率标准分的偏度:%s' % (stew1))
print('斜率标准分的峰度:%s' % (kurtosis1))
print('')
print('斜率标准分的均值:%s' % (data['RSRS_R2'].mean()))
print('斜率标准分的标准差:%s' % (data['RSRS_R2'].std()))
print('斜率标准分的偏度:%s' % (stew2))
print('斜率标准分的峰度:%s' % (kurtosis2))


def RSRS1(data, S1=1.02, S2=0.6):
    data1 = data.copy()
    data1['flag'] = 0  # 买卖标记
    data1['position'] = 0  # 持仓标记
    position = 0  # 是否持仓，持仓：1，不持仓：0
    for i in range(1, data1.shape[0] - 1):

        # 开仓
        if (data1.loc[i, 'beta'] > S1 and (data1.loc[i,'MA']>data1.loc[i-1,'MA'] and data1.loc[i,'close']>data1.loc[i,'MA'])) and position == 0:
            data1.loc[i, 'flag'] = 1
            data1.loc[i + 1, 'position'] = 1
            position = 1
        # 平仓
        elif data1.loc[i, 'beta'] < S2  and position == 1:

            data1.loc[i, 'flag'] = -1
            data1.loc[i + 1, 'position'] = 0
            position = 0

        # 保持
        else:
            data1.loc[i + 1, 'position'] = data1.loc[i, 'position']

    data1['nav'] = (1 + data1.close.pct_change(1).fillna(0) * data1.position).cumprod()

    return (data1)
result = RSRS1(data)
num = result.flag.abs().sum()/2
nav = result.nav[result.shape[0]-1]
result['dd']=1-result['nav']/result['nav'].rolling(window=252,min_periods=1).max()
result['maxdd']=result['dd'].rolling(window=252,min_periods=1).max()
drawdown=result.maxdd[result.shape[0]-1]

print('交易次数 = ',num)
print('策略净值为= ',nav)
print('最大回撤=',drawdown)
#
xtick = np.arange(0,result.shape[0],int(result.shape[0]/7))
xticklabel = pd.Series(result.open_time[xtick])
plt.figure(figsize=(15,3))
fig = plt.axes()
plt.plot(np.arange(result.shape[0]),result.nav,label = 'RSRS1',linewidth = 2,color = 'red')
plt.plot(np.arange(result.shape[0]),result.close/result.close[0],color = 'yellow',label = 'BTC',linewidth = 2)

fig.set_xticks(xtick)
fig.set_xticklabels(xticklabel,rotation = 45)
plt.legend()
plt.show()


# def RSRS4(data, S=0.45):
#     data1 = data.copy()
#     data1['flag'] = 0  # 买卖标记
#     data1['position'] = 0  # 持仓标记
#     position = 0  # 是否持仓，持仓：1，不持仓：0
#     for i in range(1, data1.shape[0] - 1):
#
#         # 开仓
#         if data1.loc[i, 'beta_right'] > S and position == 0:
#             data1.loc[i, 'flag'] = 1
#             data1.loc[i + 1, 'position'] = 1
#             position = 1
#         # 平仓
#         elif data1.loc[i, 'beta_right'] < -S and position == 1:
#             data1.loc[i, 'flag'] = -1
#             data1.loc[i + 1, 'position'] = 0
#             position = 0
#
#         # 保持
#         else:
#             data1.loc[i + 1, 'position'] = data1.loc[i, 'position']
#
#     data1['nav'] = (1 + data1.close.pct_change(1).fillna(0) * data1.position).cumprod()
#
#     return (data1)
#
# result4 = RSRS4(data)
# num = result4.flag.abs().sum()/2
# nav = result4.nav[result4.shape[0]-1]
# ret_year = (nav - 1)
# print('交易次数 = ',num)
# print('策略净值为= ',nav)

# xtick = np.arange(0,result4.shape[0],int(result4.shape[0]/7))
# xticklabel = pd.Series(result4.open_time[xtick])
# plt.figure(figsize=(15,3))
# fig = plt.axes()
# plt.plot(np.arange(result4.shape[0]),result4.nav,label = 'RSRS4',linewidth = 2,color = 'red')
# plt.plot(np.arange(result4.shape[0]),result4.close/result4.close[0],color = 'yellow',label = 'BTC',linewidth = 2)

# fig.set_xticks(xtick)
# fig.set_xticklabels(xticklabel,rotation = 45)
# plt.legend()
# plt.show()
