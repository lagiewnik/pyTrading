import json
from math import fabs

from sqlalchemy import true

tenkan_period = 9
kijun_period = 26
senkouA_shift = 26
senkouB_period = 52
chikou_shift = 26

def tenkan_sen_calc(df, close="Close", high="High", low="Low"):
    nine_period_high = df[high].rolling(window= tenkan_period).max()
    nine_period_low = df[low].rolling(window= tenkan_period).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2

def kijun_sen_calc(df, close="Close", high="High", low="Low"):
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = df[high].rolling(window=26).max()
    period26_low = df[low].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2

def kumo_calc(df, close="Close", high="High", low="Low"):
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(senkouA_shift)
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = df[high].rolling(window=senkouB_period).max()
    period52_low = df[low].rolling(window=senkouB_period).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(senkouA_shift)

# The most current closing price plotted 26 time periods behind (optional)
def chikou_calc(df, close="Close"):
    df['chikou_span'] = df[close].shift(-chikou_shift)

def ichimoku_calculate(df):
    # calc ichimoku line
    tenkan_sen_calc(df)
    kijun_sen_calc(df)
    kumo_calc(df)
    chikou_calc(df)
    # calc  point
    tenkan_vs_kijun(df)
    price_vs_kijun(df)
    kumo_color(df)
    price_vs_kumo(df)
    s3line(df)
    cross_tenkan_kijun_vs_kumo(df)
    chikou_vs_price(df)

def tenkan_vs_kijun(df):
    """
    Return relation beetween tenkan and kijun line:
    2  - tenkan crosses up the kijun
    1 - tenkan stays above kijun
    -1 - tenkan stays under kijun
    -2 - tenkan crosses down the kijun
    """
    df.dropna(subset=["tenkan_sen",'kijun_sen'])
    df['cross_tenkan_kijun']=0

    #conditional
    tenkan_over_kijun = (df["tenkan_sen"] > df["kijun_sen"])
    tenkan_under_kijun = (df["tenkan_sen"] <= df["kijun_sen"])
    tenkan_over_kijun_prev = (df["tenkan_sen"].shift(1) > df["kijun_sen"].shift(1))
    tenkan_under_kijun_prev = (df["tenkan_sen"].shift(1) <= df["kijun_sen"].shift(1))

    df.loc[tenkan_over_kijun & tenkan_under_kijun_prev, 'cross_tenkan_kijun'] = 2
    df.loc[tenkan_over_kijun & tenkan_over_kijun_prev, 'cross_tenkan_kijun'] = 1
    df.loc[tenkan_under_kijun & tenkan_over_kijun_prev, 'cross_tenkan_kijun'] = -2
    df.loc[tenkan_under_kijun & tenkan_under_kijun_prev, 'cross_tenkan_kijun'] = -1

def price_vs_kijun(df, close="Close"):
    """
    Return relation beetween close price and kijun line:
    2  - price crosses up the kijun
    1 - price stays above kijun
    -1 - price stays under kijun
    -2 - price crosses down the kijun
    """
    df.dropna(subset=["tenkan_sen",'kijun_sen'])
    df['cross_price_kijun']=0

    #conditional
    price_over_kijun = (df[close] > df["kijun_sen"])
    price_under_kijun = (df[close] <= df["kijun_sen"])
    price_over_kijun_prev = (df[close].shift(1) > df["kijun_sen"].shift(1))
    price_under_kijun_prev = (df[close].shift(1) <= df["kijun_sen"].shift(1))

    df.loc[price_over_kijun & price_under_kijun_prev, 'cross_price_kijun'] = 2
    df.loc[price_over_kijun & price_over_kijun_prev, 'cross_price_kijun'] = 1
    df.loc[price_under_kijun & price_over_kijun_prev, 'cross_price_kijun'] = -2
    df.loc[price_under_kijun & price_under_kijun_prev, 'cross_price_kijun'] = -1

def price_vs_kumo(df, close="Close", senkouA="senkou_span_a", senkouB="senkou_span_b"):
    """
    Return relation between price and kumo
    """
    
    #TODO
    df.dropna(subset=["tenkan_sen",'kijun_sen'])
    df['price_vs_kumo']=0

    #conditional
    price_over_senkouA = (df[close] > df[senkouA])
    price_over_senkouB = (df[close] > df[senkouB])
    price_under_senkouA= (df[close] <= df[senkouA])
    price_under_senkouB= (df[close] <= df[senkouB])
    price_over_senkouA_prev = (df[close].shift(1) > df[senkouA].shift(1))
    price_over_senkouB_prev = (df[close].shift(1) > df[senkouB].shift(1))
    price_under_senkouA_prev = (df[close].shift(1) <= df[senkouA].shift(1))
    price_under_senkouB_prev = (df[close].shift(1) <= df[senkouB].shift(1))

    price_over_kumo= price_over_senkouA & price_over_senkouB
    price_in_kumo = (price_over_senkouA & price_under_senkouB) | (price_under_senkouA & price_over_senkouB)
    price_under_kumo = price_under_senkouA & price_under_senkouB
    price_over_kumo_prev= price_over_senkouA_prev & price_over_senkouB_prev
    price_in_kumo_prev = (price_over_senkouA_prev & price_under_senkouB_prev) | (price_under_senkouA_prev & price_over_senkouB_prev)
    price_under_kumo_prev = price_under_senkouA_prev & price_under_senkouB_prev

    df.loc[price_in_kumo & price_in_kumo_prev,'price_vs_kumo']=0
    df.loc[price_over_kumo & price_over_kumo_prev, 'price_vs_kumo'] = 1
    df.loc[price_in_kumo & price_under_kumo_prev, 'price_vs_kumo'] = 2
    df.loc[price_over_kumo & price_in_kumo_prev, 'price_vs_kumo'] = 3
    df.loc[price_over_kumo & price_under_kumo_prev , 'price_vs_kumo'] = 4
    df.loc[price_under_kumo_prev & price_under_kumo, 'price_vs_kumo'] = -1
    df.loc[ price_over_kumo_prev & price_in_kumo, 'price_vs_kumo'] = -2
    df.loc[price_in_kumo_prev & price_under_kumo, 'price_vs_kumo'] = -3
    df.loc[price_over_kumo_prev & price_under_kumo, 'price_vs_kumo'] = -4

def kumo_color(df):
    """
        Return:
        2 - change to a growth cloud
        1 - growth cloud
        -1 - fall cloud
        -2 - change to fall cloud
    """
    df.dropna(subset=["senkou_span_a", "senkou_span_b"])
    df['kumo_color']=0

    green_color = (df["senkou_span_a"]> df["senkou_span_b"])
    green_color_prev = (df["senkou_span_a"].shift(1)> df["senkou_span_b"].shift(1))
    red_color = (df["senkou_span_a"]<= df["senkou_span_b"])
    red_color_prev = (df["senkou_span_a"].shift(1)<= df["senkou_span_b"].shift(1))

    df.loc[green_color & red_color_prev, 'kumo_color']=2
    df.loc[green_color & green_color_prev, 'kumo_color']=1
    df.loc[red_color_prev& red_color , 'kumo_color'] = -1
    df.loc[green_color_prev & red_color, 'kumo_color'] = -2

def cross_tenkan_kijun_vs_kumo(df, cross="cross_tenkan_kijun", tenkan = "tenkan_sen", kijun = 'kijun_sen', sA = 'senkou_span_a', sB = 'senkou_span_b'):
    """
    Zwraca:
    0 - nie bylo przecięcia
    1 - przecięcie w chmurze
    2- przecięcie nad chmura
    -2 - przecięcie pod chmura
    """
    df.dropna(subset=["cross_tenkan_kijun"])
    df['cross_tk_vs_kumo']=0
    # function crossVSKumo(k, k_prev, t, t_prev, sA, sA_prev, sB, sB_prev) {
    # // zwraca 0 gdy nie było przecięcie, zwraca 2 gdy przecięcie nad, -2 pod chmurą, 1 w chmurze
    fake_x0 = 0
    fake_x1 = 1
    
    # warunek-nie było przeciecia-zwroc 0
    is_cross = (df['cross_tenkan_kijun']==2) | (df['cross_tenkan_kijun']==-2)
    df["is_cross"] = is_cross
    df.loc[is_cross, 'cross_tk_vs_kumo'] = 1
    # //Wyznacz współczynniki a i b równania y = ax + b  linii k i t 
    k_eq_a = calcFactorStraight_A(fake_x0, fake_x1, df[kijun].shift(1), df[kijun])
    k_eq_b = calcFactorStraight_B(fake_x0, fake_x1, df[kijun].shift(1), df[kijun])
    t_eq_a = calcFactorStraight_A(fake_x0, fake_x1, df[tenkan].shift(1), df[tenkan])
    t_eq_b = calcFactorStraight_B(fake_x0, fake_x1, df[tenkan].shift(1), df[tenkan])
    # // x = (b1 - b2)/(a2 - a1);
    # // y = (a2 * b1 - b2 * a1) / (a2 - a1);
    # //wyznacz punkt przeciecia k i t
    cross_x = (k_eq_b - t_eq_b) / (t_eq_a - k_eq_a)
    cross_y = (t_eq_a * k_eq_b - t_eq_b * k_eq_a) / (t_eq_a - k_eq_a)

    # console.log(cross_x + "," + cross_y)
    sA_eq_a = calcFactorStraight_A(fake_x0, fake_x1, df[sA].shift(1), df[sA])
    sA_eq_b = calcFactorStraight_B(fake_x0, fake_x1, df[sA].shift(1), df[sA])
    sB_eq_a = calcFactorStraight_A(fake_x0, fake_x1, df[sB].shift(1), df[sB])
    sB_eq_b = calcFactorStraight_B(fake_x0, fake_x1, df[sB].shift(1), df[sB])

    sA_Y = sA_eq_a * cross_x + sA_eq_b
    sB_Y = sB_eq_a * cross_x + sB_eq_b
    # console.log("SA_Y: " + sA_Y)
    # console.log("SB_Y: " + sB_Y)
    # conditional:
    cross_over_kumo = (cross_y > sA_Y) & (cross_y > sB_Y)
    cross_below_kumo = (cross_y < sA_Y) & (cross_y < sB_Y)
    df.loc[cross_over_kumo & is_cross, 'cross_tk_vs_kumo'] = 2
    df.loc[cross_below_kumo & is_cross, 'cross_tk_vs_kumo'] = -2
    # if (cross_y > sA_Y & cross_y > sB_Y) {
    #     return 10
    # }
    # else if (cross_y < sA_Y & cross_y < sB_Y) {
    #     return -10
    # }
    # else return 5

def calcFactorStraight_A(fake_x0, fake_x1, y0, y1): 
    # //wyznacza współczynniki rownania prostej y = ax + b
    # // a = (y1 - y0)/(x1 - x0);
    # // b = y0 - a * x0;
    a = (y1-y0)/(fake_x1 - fake_x0)
    #b = y0 - a*fake_x0
    
    return a

def calcFactorStraight_B(fake_x0, fake_x1, y0, y1): 
    # //wyznacza współczynniki rownania prostej y = ax + b
    # // a = (y1 - y0)/(x1 - x0);
    # // b = y0 - a * x0;
    a = (y1-y0)/(fake_x1 - fake_x0)
    b = y0 - a*fake_x0
    
    return b

def chikou_vs_price(df, chikou_span="chikou_span", close="Close"):
    """
    1 - if chikou span greater than the price in the candle shifted by the chikou period
    -1 - if chikou span less than the price in the candle shifted by the chikou period

    """
    df.dropna(subset=[chikou_span])
    df['chikou_span_vs_price']=0
    chikou_over = df[chikou_span] > df[close].shift(chikou_shift)
    chikou_under = df[chikou_span] < df[close].shift(chikou_shift)

def s3line(df, tenkan="tenkan_sen", kijun="kijun_sen", senkouA = "senkou_span_a" ):
    """TODO"""
    df.dropna(subset=[senkouA, kijun, tenkan])
    df['s3line']=0

    s3_up = (df[tenkan] > df[kijun]) & (df[kijun] > df[senkouA])
    s3_down = (df[tenkan] <= df[kijun]) & (df[kijun] <= df[senkouA])
    s3_up_prev = (df[tenkan].shift(1) > df[kijun].shift(1)) & (df[kijun].shift(1) > df[senkouA].shift(1))
    s3_down_prev = (df[tenkan].shift(1) <= df[kijun].shift(1)) & (df[kijun].shift(1) <= df[senkouA].shift(1))

    df.loc[s3_up & s3_up_prev ,'s3line']= 1
    df.loc[s3_up & ~(s3_up_prev) ,'s3line']= 2
    df.loc[s3_down & s3_down_prev ,'s3line']= -1
    df.loc[s3_down & ~(s3_down_prev) ,'s3line']= -2

def test():
    print("TEST")