import ccxt
import pandas as pd
import numpy as np
import datetime
import time
import threading
from pprint import pprint
from BotRSI_config import *
from colorama import Fore, Style
import pickle
import logging
import os
logging.basicConfig(filename='bot_logs.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

### VERSION V12_20240924
# MODIFICACIONES: TRAILING STOP OPTIMIZADO
#                 PRIMERA ORDEN POR COSTO EN DOLARES
#                 AMOUNT REDONDEADO SI SYMBOL ES MENOR A COSTO
#                 VARIABLE NEXT LONG-SHORT
#                 AJUSTE GUARDADO ARCHIVO PICKLE
#                 CORRECCION PRINT APERTURA ORDENES
#                 CORRECCION CALCULO HIGH-LOW SOLO PARA POSICIONES ABIERTAS - 2
#                 AGREGA VALIDACIONES PARA ACTIVAR SHORT Y/O LONG
#                 CORRECCION CALCULO HIGH-LOW SOLO PARA POSICIONES ABIERTAS - 3
#                 AGREGA PARAMETRO DE INCREMENTO DE ORDENES PARA LONG Y SHORT SEPARADOS
#                 CONTROL DESDE CONFIG PARA ACTIVAR CIERRE DE ORDENES EN LONG Y SHORT

class trader():
    def __init__(self, symbol, cost, sl, tp, even, tradecount_limit, incre_price_percent_long, incre_price_percent_short, incre_amt_percent_long, incre_amt_percent_short, timeframe):
        # Inicializar con valores predeterminados
        self.initialize_default_state(symbol, cost, sl, tp, even, tradecount_limit, incre_price_percent_long, incre_price_percent_short, incre_amt_percent_long, incre_amt_percent_short, timeframe)
        
        # Verificar si el archivo 'trader_state.pickle' existe
        if os.path.exists('trader_state.pickle'):
            try:
                with open('trader_state.pickle', 'rb') as handle:
                    state = pickle.load(handle)
                    self.set_state(state)
                logging.info('Estado cargado exitosamente desde trader_state.pickle')
            except Exception as e:
                logging.error(f'Error al cargar el estado: {e}')
                self.save_state()
        else:
            self.save_state()
            
    def initialize_default_state(self, symbol, cost, sl, tp, even, tradecount_limit, incre_price_percent_long, incre_price_percent_short, incre_amt_percent_long, incre_amt_percent_short, timeframe):
        self.trader_id = 0
        self.symbol = symbol
        self.last_price = self.get_last_price(ex, self.symbol)
        self.amount = cost / self.last_price
        self.total_amount_long = self.amount
        self.total_amount_short = self.amount
        self.side = None
        self.sl = sl
        self.tp = tp
        self.even = even
        self.buy_sl_price = 0
        self.buy_tp_price = 0
        self.sell_sl_price = 10000000  # modificado 0
        self.sell_tp_price = 0
        self.last_buy_price = 0
        self.last_sell_price = 0
        self.last_trade_side = None
        self.buycount = 0
        self.sellcount = 0
        self.tradecount_long = 0
        self.tradecount_short = 0
        self.tradecount_limit = tradecount_limit
        self.incre_price_percent_long = incre_price_percent_long
        self.incre_price_percent_short = incre_price_percent_short
        self.incre_amt_percent_long = incre_amt_percent_long
        self.incre_amt_percent_short = incre_amt_percent_short
        self.timeframe = timeframe
        self.current_close = 0
        self.current_rsi = 0
        self.buy_active = False
        self.sell_active = False
        self.buy_first_order = True
        self.sell_first_order = True
        self.buy_count = 0
        self.sell_count = 0
        self.current_high1 = 0
        self.current_low1 = 0
        self.order_amount_long = 0
        self.order_amount_short = 0
        self.next_buy_long = 0
        self.next_sell_short = 0

    def set_state(self, state):
        self.trader_id = state.get('Trade_id', self.trader_id)
        self.symbol = state.get('Symbol', self.symbol)
        self.last_price = state.get('Last_price', self.last_price)
        self.amount = state.get('Initial_amount', self.amount)
        self.total_amount_long = state.get('Total_amount_long', self.total_amount_long)
        self.total_amount_short = state.get('Total_amount_short', self.total_amount_short)
        self.side = state.get('Side', self.side)
        self.sl = state.get('Sl', self.sl)
        self.tp = state.get('Tp', self.tp)
        self.even = state.get('Even', self.even)
        self.buy_sl_price = state.get('Buy_sl_price', self.buy_sl_price)
        self.buy_tp_price = state.get('Buy_tp_price', self.buy_tp_price)
        self.sell_sl_price = state.get('Sell_sl_price', self.sell_sl_price)
        self.sell_tp_price = state.get('Sell_tp_price', self.sell_tp_price)
        self.last_buy_price = state.get('Buy_price_long', self.last_buy_price)
        self.last_sell_price = state.get('Sell_price_short', self.last_sell_price)
        self.last_trade_side = state.get('Last_trade_side', self.last_trade_side)
        self.buycount = state.get('Buy_count', self.buycount)
        self.sellcount = state.get('Sell_count', self.sellcount)
        self.tradecount_long = state.get('Trade_count_long', self.tradecount_long)
        self.tradecount_short = state.get('Trade_count_short', self.tradecount_short)        
        self.tradecount_limit = state.get('Tradecount_limit', self.tradecount_limit)
        self.incre_price_percent_long = state.get('Incremental_price_percent_long', self.incre_price_percent_long)
        self.incre_amt_percent_long = state.get('Incremental_amount_percent_long', self.incre_amt_percent_long)
        self.incre_price_percent_short = state.get('Incremental_price_percent_short', self.incre_price_percent_short)
        self.incre_amt_percent_short = state.get('Incremental_amount_percent_short', self.incre_amt_percent_short)
        self.timeframe = state.get('Timeframe', self.timeframe)
        self.current_close = state.get('Current_close', self.current_close)
        self.current_rsi = state.get('Current_rsi', self.current_rsi)
        self.buy_active = state.get('Buy_active', self.buy_active)
        self.sell_active = state.get('Sell_active', self.sell_active)
        self.buy_first_order = state.get('Buy_first_order', self.buy_first_order)
        self.sell_first_order = state.get('Sell_first_order', self.sell_first_order)
        self.buy_count = state.get('Compra_long_numero', self.buy_count)
        self.sell_count = state.get('Compra_short_numero', self.sell_count)
        self.current_high1 = state.get('Current_high1', self.current_high1)
        self.current_low1 = state.get('Current_low1', self.current_low1)
        self.order_amount_long = state.get('Order_amount_long', self.order_amount_long)
        self.order_amount_short = state.get('Order_amount_short', self.order_amount_short)
        self.next_buy_long = state.get('Next_long', self.next_buy_long)
        self.next_sell_short = state.get('Next_short', self.next_sell_short)

    #  Function to save all states of trader class
    def get_state(self):
        # save all variables
        return {
            'Trade_id': self.trader_id,
            'Symbol': self.symbol,
            'Last_price': self.last_price,
            #'Initial_amount': self.amount, # no se guarda este valor en archivo pickle
            'Total_amount_long': self.total_amount_long,
            'Total_amount_short': self.total_amount_short,
            'Side': self.side,
            #'Sl': self.sl,
            #'Tp': self.tp,
            #'Even': self.even,
            'Buy_sl_price': self.buy_sl_price,
            'Buy_tp_price': self.buy_tp_price,
            'Sell_sl_price': self.sell_sl_price,
            'Sell_tp_price': self.sell_tp_price,
            'Buy_price_long': self.last_buy_price,
            'Sell_price_short': self.last_sell_price,
            'Last_trade_side': self.last_trade_side,
            'Buy_count': self.buycount,
            'Sell_count': self.sellcount,
            'Trade_count_long': self.tradecount_long,
            'Trade_count_short': self.tradecount_short,
            'Tradecount_limit': self.tradecount_limit,
            #'Incremental_price_percent_long': self.incre_price_percent_long,
            #'Incremental_price_percent_short': self.incre_price_percent_short,
            #'Incremental_amount_percent_long': self.incre_amt_percent_long,
            #'Incremental_amount_percent_short': self.incre_amt_percent_short,
            #'Timeframe': self.timeframe,
            'Current_close': self.current_close,
            'Current_rsi': self.current_rsi,
            'Buy_active': self.buy_active,
            'Sell_active': self.sell_active,
            'Buy_first_order': self.buy_first_order,
            'Sell_first_order': self.sell_first_order,
            'Compra_long_numero': self.buy_count,
            'Compra_short_numero': self.sell_count,
            'Current_high1': self.current_high1,
            'Current_low1': self.current_low1,
            'Order_amount_long': self.order_amount_long,
            'Order_amount_short': self.order_amount_short,
            'Next_long': self.next_buy_long,
            'Next_short': self.next_sell_short,
        }

    # save state
    def save_state(self):
        with open('trader_state.pickle', 'wb') as handle:
            pickle.dump(self.get_state(), handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

    # load state
    def load_state(self):
        with open('trader_state.pickle', 'rb') as handle:
            logging.info('loading state')
            self.set_state(pickle.load(handle))

    def parse_dates(self, ts):
        return datetime.datetime.fromtimestamp(ts/1000.0)

    def SMA(self, series, period):
        sma0 = series.rolling(window=period).mean()
        return sma0

    def EMA(self, series, period):
        ema0 = series.ewm(span=period, adjust=False).mean()
        return ema0

    def WMA(self, series, period):
        d = (period * (period + 1)) / 2  # denominator
        weights = pd.Series(np.arange(1, period + 1))

        def linear(w):
            def _compute(x):
                return (w * x).sum() / d

            return _compute

        _close = series.rolling(period, min_periods=period)
        wma0 = _close.apply(linear(weights), raw=True)
        return wma0

    def RSI(self, series, period):
        # delta = series.diff().dropna()
        delta = series.diff()
        u, d = delta.copy(), delta.copy()
        u[u < 0] = 0
        d[d > 0] = 0

        # Calculate the EWMA
        _gain = u.ewm(alpha=1/period).mean()
        _loss = d.abs().ewm(alpha=1/period).mean()

        # Calculate the RSI based on EWMA
        rs = _gain / _loss
        rs0 = 100.0 - (100.0 / (1.0 + rs))
        return rs0

    def RSI2(self, ohlc, period=14, column="close", adjust=True):
        # get the price diff
        delta = ohlc[column].diff()

        # positive gains (up) and negative gains (down) Series
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        # EMAs of ups and downs
        _gain = up.ewm(alpha=1.0 / period, adjust=adjust).mean()
        _loss = down.abs().ewm(alpha=1.0 / period, adjust=adjust).mean()

        RS = _gain / _loss
        return pd.Series(100 - (100 / (1 + RS)), name="{0} period RSI".format(period))

    def get_last_price(self, ex, symbol):
        # obtener el ultimo precio de mercado
        ticker = ex.fetch_ticker(symbol)
        last_market_price = ticker['last']
        return last_market_price

    def get_market_data(self, ex, symbol, timeframe):
        # Getdata
        data = ex.fetch_ohlcv(symbol, timeframe, limit=200)
        df = pd.DataFrame(data)
        df.columns = (['ndatetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = df['ndatetime'].apply(self.parse_dates)

        # ohlc
        ohlc = df[['datetime', 'open', 'high', 'low', 'close']].copy()
        ohlc.set_index('datetime', drop=True, inplace=True)
        return ohlc

    def close_last_trade_long(self, side):
        # create market-order
        try:
            fecha_actual = datetime.datetime.now()
            fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
            result = ex.create_order(
                self.symbol, 'market', side, self.total_amount_long, params={"reduceOnly": True})
            # print(f'{Fore.WHITE}current_rsi:', self.current_rsi)
            print(
                f'{Fore.WHITE}\nCLOSE LONG\nDate: {fecha_formateada}\nSymbol: {self.symbol}\nOrder: {side}\nHigh Price: {self.current_high1}\nAmount: {self.total_amount_long}\n')
            # print(fecha_formateada)
            logging.info(
                f'CERRANDO LONG DE {self.symbol}, CON {self.buy_count} ENTRADAS')
        except Exception as e:
            logging.error(e)
            print(e)

            print(
                f'!!! [STOP-LOSS] CANNOT Close Trade for {self.symbol} == [{side}] ... Please Check Account\n')

    def close_last_trade_short(self, side):
        # create market-order
        try:
            fecha_actual = datetime.datetime.now()
            fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
            result = ex.create_order(
                self.symbol, 'market', side, self.total_amount_short, params={"reduceOnly": True})
            # print(f'{Fore.WHITE}current_rsi:', self.current_rsi)
            print(
                f'{Fore.WHITE}\nCLOSE SHORT\nDate: {fecha_formateada}\nSymbol: {self.symbol}\nOrder: {side}\nLow Price: {self.current_low1}\nAmount: {self.total_amount_short}\n')
            # print(fecha_formateada)
            logging.info(
                f'CERRANDO SHORT DE {self.symbol} CON {self.sell_count} ENTRADAS')
        except Exception as e:
            logging.error(e)
            print(e)

            print(
                f'!!! [STOP-LOSS] CANNOT Close Trade for {self.symbol} == [{side}] ... Please Check Account\n')

    def create_trade(self):
        # Calcular las cantidades de orden antes de los bloques if/elif
        self.order_amount_long = self.amount * (1 + (self.incre_amt_percent_long * self.buycount))
        self.order_amount_short = self.amount * (1 + (self.incre_amt_percent_short * self.sellcount))
                # create market-order
        try:
            if self.side == 'buy':
                result = ex.create_order(
                    self.symbol, 'market', self.side, self.order_amount_long)
            elif self.side == 'sell':
                result = ex.create_order(
                    self.symbol, 'market', self.side, self.order_amount_short)

            res = ex.fetch_positions([self.symbol])
            if self.side == 'buy' and res[-1]['side'] == 'long':
                result = res[-1]
            elif self.side == 'buy' and res[-2]['side'] == 'long':
                result = res[-2]
            elif self.side == 'sell' and res[-1]['side'] == 'short':
                result = res[-1]
            elif self.side == 'sell' and res[-2]['side'] == 'short':
                result = res[-2]
            else:
                print('!!! major error = check entry mode....')

            if self.side == 'buy':
                self.tradecount_long += 1
            elif self.side == 'sell':
                self.tradecount_short += 1
            if self.side == 'buy':
                self.total_amount_long = float(result['contracts'])
            elif self.side == 'sell':
                self.total_amount_short = float(result['contracts'])

            if self.side == 'buy':
                self.buy_sl_price = float(result['entryPrice']) * (1-self.sl)
                self.buy_tp_price = float(result['entryPrice']) * (1+self.tp)
                self.buycount += 1
                self.buy_count += 1
                self.last_buy_price = float(result['entryPrice'])
                self.buy_active = True
                fecha_actual = datetime.datetime.now()
                fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
                # print(f'{Fore.BLUE}current_rsi:', self.current_rsi)
                print(f'{Fore.GREEN}\nBuy number: {self.buy_count}\nDate: {fecha_formateada}\nRsi: {self.current_rsi}\nSymbol: {self.symbol}\nSide: {self.side}\nAmount: {self.order_amount_long}\nBuy_sl_price: {self.buy_sl_price}\nBuy_tp_price: {self.buy_tp_price}\n')
               # print(fecha_formateada)
                logging.info(
                    f'Compra Long Numero: {self.buy_count}, Symbol: {self.symbol}, Side: {self.side}, Amount: {self.amount}, Buy_sl_price: {self.buy_sl_price}, Buy_tp_price: {self.buy_tp_price}')

            elif self.side == 'sell':
                self.sell_sl_price = float(result['entryPrice']) * (1+self.sl)
                self.sell_tp_price = float(result['entryPrice']) * (1-self.tp)
                self.sellcount += 1
                self.sell_count += 1
                self.last_sell_price = float(result['entryPrice'])
                self.sell_active = True
                fecha_actual = datetime.datetime.now()
                fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
                # print(f'{Fore.BLUE}current_rsi:', self.current_rsi)
                print(f'{Fore.RED}\nSell number: {self.sell_count}\nDate: {fecha_formateada}\nRsi: {self.current_rsi}\nSymbol: {self.symbol}\nSide: {self.side}\nAmount: {self.order_amount_short}\nSell_sl_price: {self.sell_sl_price}\nSell_tp_price: {self.sell_tp_price}\n')
                # print(fecha_formateada)
                logging.info(
                    f'Compra Short Numero: {self.sell_count}, Symbol: {self.symbol}, Side: {self.side}, Amount: {self.amount}, Sell_sl_price: {self.sell_sl_price}, Sell_tp_price: {self.sell_tp_price}')
            # Save State
            self.save_state()

        except Exception as e:
            print(e)
            logging.error(e)
            print(
                f'!!! UNABLE to Create Trade for {self.symbol} == [{self.side}] ... Please Check Account\n')

    def strategy_check(self):
        try:
            # load ohlc data of a market
            # ohlc_1m = self.get_market_data(ex, self.symbol, '1m')
            ohlc_tf = self.get_market_data(
                ex, self.symbol, self.timeframe)  # self.timeframe

            # get indicators values
            rsi_tf = self.RSI(ohlc_tf[SOURCE], RSI_PERIOD)

            # obtener el ultimo precio
            self.last_price = self.get_last_price(ex, self.symbol)

            # check strategy
            self.current_close = self.last_price
            self.current_high = self.last_price
            self.current_low = self.last_price

            if self.last_buy_price > 0 and self.current_high < (self.last_buy_price*(1+(self.tp-self.even))):
                self.current_high1 = 0
            elif self.last_buy_price > 0 and self.current_high >= (self.last_buy_price*(1+(self.tp-self.even))):
                if self.current_high > self.current_high1:
                    self.current_high1 = self.current_high  # modificado
            else:
                if self.current_high1 == 0:
                    self.current_high1 = 0
            
            if self.last_sell_price > 0 and self.current_low > (self.last_sell_price*(1-(self.tp-self.even))):
                self.current_low1 = 0
            elif self.last_sell_price > 0 and self.current_low <= (self.last_sell_price*(1-(self.tp-self.even))):
                if self.current_low1 == 0 or self.current_low < self.current_low1:
                    self.current_low1 = self.current_low
            else:
                if self.current_low1 == 0:
                    self.current_low1 = 0
            self.current_rsi = round(rsi_tf[-1], 2)

            self.next_buy_long = (self.last_buy_price*(1-(self.incre_price_percent_long*self.buycount)))
            self.next_sell_short = (self.last_sell_price*(1+(self.incre_price_percent_short*self.sellcount)))

            # print(f'{Fore.BLUE}current_rsi:', self.current_rsi, 'current_close:', self.current_close, 'self.current_high1:' , self.current_high1, 'self.current_low1:' , self.current_low1)

            if (self.current_high1 >= self.last_buy_price*(1+self.tp)) and (self.current_close >= self.buy_tp_price) and self.buy_active:
                self.buy_sl_price = self.current_high1*(1-self.even)  # sl = precio mas alto registrado * 1-distancia retroceso
                self.buy_tp_price = self.last_buy_price*(1+(self.tp-self.even)) # distancia en long al que se activa el BE en profit
                #print(f'{Fore.GREEN}Breakeven: ', self.buy_sl_price, ' - Ultimo precio:', self.current_high1)
                logging.info(f'Breakeven: {self.buy_sl_price}')

            elif (self.current_low1 <= self.last_sell_price*(1-self.tp)) and (self.current_close <= self.sell_tp_price) and self.sell_active:
                self.sell_sl_price = self.current_low1*(1+self.even)  # distancia permitida para cerrar operacion en market despues de activar el BE
                self.sell_tp_price = self.last_sell_price*(1-(self.tp-self.even))  # distancia en short al que se activa el BE en profit
                #print(f'{Fore.RED}Breakeven: ', self.sell_sl_price, ' - Ultimo precio:', self.current_low1)
                logging.info(f'Breakeven: {self.sell_sl_price}')

            if (self.current_close <= self.buy_sl_price) and self.buy_active and CLOSE_LONG == True:
                self.close_last_trade_long('sell')  # aqui cerrar todo
                fecha_actual = datetime.datetime.now()
                fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
                # print(fecha_formateada)
                print('Close Long Price: ', self.buy_sl_price)
                logging.info(f'Orden cierre Long: {self.buy_sl_price}')
                self.buy_active = False
                self.buy_first_order = True  # cambio mio
                self.next_buy_long = 0
                self.buycount = 0
                self.tradecount_long = 0
                self.buy_sl_price = 0
                self.current_high1 = 0
                self.last_buy_price = 0
                self.buy_count = 0
                self.buy_tp_price = 0
                self.total_amount_long = 0
                self.order_amount_long = 0
                
            elif (self.current_close >= self.sell_sl_price) and self.sell_active and CLOSE_SHORT == True:
                self.close_last_trade_short('buy')  # aqui cerrar todo
                fecha_actual = datetime.datetime.now()
                fecha_formateada = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
                # print(fecha_formateada)
                print('Close Short Price: ', self.sell_sl_price)
                logging.info(f'Orden cierre Short: {self.sell_sl_price}')
                self.sell_active = False
                self.sell_first_order = True  # cambio mio
                self.next_sell_short = 0
                self.tradecount_short = 0
                self.sellcount = 0
                self.last_sell_price = 0
                self.sell_sl_price = 10000000
                self.current_low1 = 0
                self.sell_count = 0
                self.sell_tp_price = 0
                self.total_amount_short = 0
                self.order_amount_short = 0

                
            if ((self.tradecount_long + self.tradecount_short) < self.tradecount_limit) or (self.tradecount_limit == 0):
                if self.current_rsi <= RSI_LOWER and ACTIVATE_LONG == True:   # long
                    if (INCREMENTAL_ORDER and (self.buy_first_order or (self.current_close < self.next_buy_long))) or (not INCREMENTAL_ORDER):
                        self.buy_first_order = False
                        self.side = 'buy'
                        self.create_trade()
                        fecha_actual = datetime.datetime.now()
                        fecha_formateada = fecha_actual.strftime(
                            "%Y-%m-%d %H:%M:%S")
                        # print(fecha_formateada)
                        # print(f'{Fore.YELLOW}current_rsi:', self.current_rsi)
                        print(f'{Fore.GREEN}Date:', (fecha_formateada), '-- Long_Position_Price:', self.last_buy_price, '-- Total_Long_Amount:', self.total_amount_long)
                        logging.info(
                            f'Precio_promedio_long: {self.last_buy_price} Total contratos comprados: {self.total_amount_long}')

                elif self.current_rsi > RSI_UPPER and ACTIVATE_SHORT == True:   # short
                    if (INCREMENTAL_ORDER and (self.sell_first_order or (self.current_close > self.next_sell_short))) or (not INCREMENTAL_ORDER):
                        self.sell_first_order = False
                        self.side = 'sell'
                        self.create_trade()
                        fecha_actual = datetime.datetime.now()
                        fecha_formateada = fecha_actual.strftime(
                            "%Y-%m-%d %H:%M:%S")
                        # print(fecha_formateada)
                        # print(f'{Fore.YELLOW}current_rsi:', self.current_rsi)
                        print(f'{Fore.RED}Date:', (fecha_formateada), '-- Short_Position_Price:', self.last_sell_price, '-- Total_Short_Amount:', self.total_amount_short)
                        logging.info(
                            f'Precio_compra_short: {self.last_sell_price} Total contratos vendidos: {self.total_amount_short}')
            # Save State
            self.save_state()
        except Exception as e:
            logging.error(e)
            # print(e)
            time.sleep(3)

    def trade_manager(self):
        if self.timeframe == '1m':
            timecheck = [i for i in range(0, 59)]
        elif self.timeframe == '3m':
            timecheck = [i for i in range(0, 59, 3)]
        elif self.timeframe == '5m':
            timecheck = [i for i in range(0, 59, 5)]
        elif self.timeframe == '15m':
            timecheck = [i for i in range(0, 59, 15)]
        elif self.timeframe == '1h':
            timecheck = [i for i in range(0, 59, 60)]
        elif self.timeframe == '4h':
            timecheck = [i for i in range(0, 59, 240)]
        lasttime = localtime[5]

        while True:
            if localtime[5] != lasttime:
                lasttime = localtime[5]
                if localtime[5] in timecheck:
                    self.strategy_check()

            time.sleep(3)
        return True


def main():
    global ex, bottrader, localtime

    # load exchange
    print('Loading Exchange...')
    logging.info('Loading Exchange...')
    ex = ccxt.bitget({'apiKey': API_KEY, 'secret': SECRET_KEY,
                     'password': PASSWORD, 'enableRateLimit': True})
    ex.options['defaultType'] = 'future'
    ex.set_sandbox_mode(False)

    # Initializations
    print('Initializing Variables...')
    logging.info('Initializing Variables...')
    bottrader = {}
    localtime = time.localtime(time.time())

    # Create Traders
    print('Creating Trades...')
    logging.info('Creating Trades...')
    for i in range(len(SYMBOLS)):
        print(f'--trade {i}: {SYMBOLS[i]}')
        bottrader[SYMBOLS[i]] = trader(SYMBOLS[i], COST[i], STOPLOSS_PERCENT[i], TAKEPROFIT_PERCENT[i], BREAKEVEN_CLOSE[i],
                                       TRADE_COUNT_LIMIT[i], INCREMENTAL_PRICE_PERCENT_LONG[i], INCREMENTAL_PRICE_PERCENT_SHORT[i], INCREMENTAL_AMT_PERCENT_LONG[i], INCREMENTAL_AMT_PERCENT_SHORT[i], TIMEFRAME)

        # ================================================
        x1 = threading.Thread(
            target=bottrader[SYMBOLS[i]].trade_manager, args=())
        x1.daemon = True
        x1.start()
        # ================================================

    print('Bot Started... running\n')
    logging.info('Bot Started... running\n')
    while True:
        localtime = time.localtime(time.time())
        time.sleep(3)


main()
