import datetime
import math
import pytz

# Global lists to store drawing objects for conceptual visualization
labels_to_draw = []
boxes_to_draw = []
lines_to_draw = []
candles_to_draw = []

class PineScriptEmulator:
    def __init__(self):
        self.data = []
        self.bar_index = 0
        self.time = []
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.volume = []
        self.tr_series = []
        self.time_close = []
        self.highs_raw = [] # Corresponds to Pine Script's 'highs' array
        self.lows_raw = []  # Corresponds to Pine Script's 'lows' array
        self.times_raw = [] # Corresponds to Pine Script's 'times' array

    def get_data_at_index(self, index):
        if 0 <= index < len(self.data):
            return self.data[index]
        return None

    def get_series_value(self, series, offset):
        if isinstance(series, list):
            idx = self.bar_index - offset
            if 0 <= idx < len(series):
                return series[idx]
        if offset == 0:
            return series
        return float('nan') # Pine Script's 'na'

    def ta_atr(self, length):
        # Average True Range calculation
        if self.bar_index < length:
            return float('nan')
        
        if len(self.tr_series) < self.bar_index + 1:
            return float('nan') # Not enough TR values calculated yet

        sum_tr = 0.0
        count = 0
        for i in range(length):
            idx = self.bar_index - i
            if idx >= 0 and idx < len(self.tr_series) and not math.isnan(self.tr_series[idx]):
                sum_tr += self.tr_series[idx]
                count += 1
            else:
                return float('nan') # Not enough historical data or NaN in series
        return sum_tr / count if count > 0 else float('nan')

    def ta_highest(self, series, length):
        # Highest value in a lookback window
        if not isinstance(series, list) or self.bar_index < length - 1:
            return float('nan')
        
        highest_val = float('-inf')
        found_valid = False
        for i in range(length):
            val = self.get_series_value(series, i)
            if not math.isnan(val):
                highest_val = math.max(highest_val, val)
                found_valid = True
        return highest_val if found_valid else float('nan')

    def ta_lowest(self, series, length):
        # Lowest value in a lookback window
        if not isinstance(series, list) or self.bar_index < length - 1:
            return float('nan')
        
        lowest_val = float('inf')
        found_valid = False
        for i in range(length):
            val = self.get_series_value(series, i)
            if not math.isnan(val):
                lowest_val = math.min(lowest_val, val)
                found_valid = True
        return lowest_val if found_valid else float('nan')

    def ta_change(self, series):
        prev_val = self.get_series_value(series, 1)
        curr_val = self.get_series_value(series, 0)
        if not math.isnan(prev_val) and not math.isnan(curr_val):
            return curr_val - prev_val
        return float('nan')

    def ta_crossover(self, series1, series2):
        val1_prev = self.get_series_value(series1, 1)
        val2_prev = self.get_series_value(series2, 1)
        val1_curr = self.get_series_value(series1, 0)
        val2_curr = self.get_series_value(series2, 0)
        if not math.isnan(val1_prev) and not math.isnan(val2_prev) and \
           not math.isnan(val1_curr) and not math.isnan(val2_curr):
            return val1_prev < val2_prev and val1_curr > val2_curr
        return False

    def ta_crossunder(self, series1, series2):
        val1_prev = self.get_series_value(series1, 1)
        val2_prev = self.get_series_value(series2, 1)
        val1_curr = self.get_series_value(series1, 0)
        val2_curr = self.get_series_value(series2, 0)
        if not math.isnan(val1_prev) and not math.isnan(val2_prev) and \
           not math.isnan(val1_curr) and not math.isnan(val2_curr):
            return val1_prev > val2_prev and val1_curr < val2_curr
        return False

    def ta_cum(self, series):
        # Cumulative sum of a series
        if not isinstance(series, list) or len(series) == 0:
            return float('nan')
        
        # Sum up values from the beginning of the series to the current bar_index
        current_sum = 0.0
        for i in range(self.bar_index + 1):
            if i < len(series) and not math.isnan(series[i]):
                current_sum += series[i]
            else:
                # If any value in the history is NaN, the cumulative sum becomes NaN
                return float('nan')
        return current_sum

    def ta_tr(self):
        # True Range calculation: max(high - low, abs(high - close[1]), abs(low - close[1]))
        if self.bar_index == 0:
            return self.get_series_value(self.high, 0) - self.get_series_value(self.low, 0) # First bar, no previous close
        
        current_high = self.get_series_value(self.high, 0)
        current_low = self.get_series_value(self.low, 0)
        prev_close = self.get_series_value(self.close, 1)

        if math.isnan(current_high) or math.isnan(current_low) or math.isnan(prev_close):
            return float('nan')

        range1 = current_high - current_low
        range2 = abs(current_high - prev_close)
        range3 = abs(current_low - prev_close)
        return max(range1, range2, range3)

    def ta_sma(self, src_series, length):
        if not isinstance(src_series, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)
        
        sma_values = [float('nan')] * (self.bar_index + 1)
        for i in range(length - 1, self.bar_index + 1):
            start_idx = i - length + 1
            window = src_series[start_idx : i + 1]
            if len(window) == length and all(not math.isnan(x) for x in window):
                sma_values[i] = sum(window) / length
        return sma_values

    def ta_ema(self, src_series, length):
        if not isinstance(src_series, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)

        ema_values = [float('nan')] * (self.bar_index + 1)
        alpha = 2 / (length + 1)

        initial_sum = 0.0
        initial_count = 0
        for i in range(length):
            if i < len(src_series) and not math.isnan(src_series[i]):
                initial_sum += src_series[i]
                initial_count += 1
        
        if initial_count == length:
            ema_values[length - 1] = initial_sum / length
        else:
            return [float('nan')] * (self.bar_index + 1)

        for i in range(length, self.bar_index + 1):
            current_src = src_series[i]
            prev_ema = ema_values[i-1]
            if not math.isnan(current_src) and not math.isnan(prev_ema):
                ema_values[i] = alpha * current_src + (1 - alpha) * prev_ema
            else:
                ema_values[i] = float('nan')
        return ema_values

    def ta_wma(self, src_series, length):
        if not isinstance(src_series, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)

        wma_values = [float('nan')] * (self.bar_index + 1)
        weights_sum = length * (length + 1) / 2

        for i in range(length - 1, self.bar_index + 1):
            weighted_sum = 0.0
            valid_count = 0
            for j in range(length):
                idx = i - j
                if idx >= 0 and not math.isnan(src_series[idx]):
                    weighted_sum += src_series[idx] * (length - j)
                    valid_count += 1
            
            if valid_count == length:
                wma_values[i] = weighted_sum / weights_sum
            else:
                wma_values[i] = float('nan')
        return wma_values

    def ta_hma(self, src_series, length):
        # Hull Moving Average (HMA)
        # HMA = WMA(2*WMA(src, len/2) - WMA(src, len), sqrt(len))
        if not isinstance(src_series, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)

        half_length = int(length / 2)
        wma1_series = self.ta_wma(src_series, half_length)
        wma2_series = self.ta_wma(src_series, length)

        diff_series = [float('nan')] * (self.bar_index + 1)
        for i in range(self.bar_index + 1):
            wma1_val = self.get_series_value(wma1_series, self.bar_index - i)
            wma2_val = self.get_series_value(wma2_series, self.bar_index - i)
            if not math.isnan(wma1_val) and not math.isnan(wma2_val):
                diff_series[i] = 2 * wma1_val - wma2_val
            else:
                diff_series[i] = float('nan')
        
        hma_values = self.ta_wma(diff_series, int(math.sqrt(length)))
        return hma_values

    def ta_vwma(self, src_series, length):
        if not isinstance(src_series, list) or not isinstance(self.volume, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)

        vwma_values = [float('nan')] * (self.bar_index + 1)

        for i in range(length - 1, self.bar_index + 1):
            price_volume_sum = 0.0
            volume_sum = 0.0
            valid_count = 0
            for j in range(length):
                idx = i - j
                if idx >= 0 and not math.isnan(src_series[idx]) and not math.isnan(self.volume[idx]):
                    price_volume_sum += src_series[idx] * self.volume[idx]
                    volume_sum += self.volume[idx]
                    valid_count += 1
            
            if valid_count == length and volume_sum != 0:
                vwma_values[i] = price_volume_sum / volume_sum
            else:
                vwma_values[i] = float('nan')
        return vwma_values

    def ta_rma(self, src_series, length):
        if not isinstance(src_series, list) or self.bar_index < length - 1:
            return [float('nan')] * (self.bar_index + 1)

        rma_values = [float('nan')] * (self.bar_index + 1)
        alpha = 1 / length

        initial_sum = 0.0
        initial_count = 0
        for i in range(length):
            if i < len(src_series) and not math.isnan(src_series[i]):
                initial_sum += src_series[i]
                initial_count += 1
        
        if initial_count == length:
            rma_values[length - 1] = initial_sum / length
        else:
            return [float('nan')] * (self.bar_index + 1)

        for i in range(length, self.bar_index + 1):
            current_src = src_series[i]
            prev_rma = rma_values[i-1]
            if not math.isnan(current_src) and not math.isnan(prev_rma):
                rma_values[i] = alpha * current_src + (1 - alpha) * prev_rma
            else:
                rma_values[i] = float('nan')
        return rma_values

    def ta_pivothigh(self, source, leftbars, rightbars):
        # Pivot high detection
        # source is expected to be a list (e.g., self.high)
        if not isinstance(source, list) or self.bar_index < leftbars + rightbars:
            return float('nan')

        current_bar_val = self.get_series_value(source, 0)
        if math.isnan(current_bar_val):
            return float('nan')

        is_pivot = True
        # Check left bars
        for i in range(1, leftbars + 1):
            left_val = self.get_series_value(source, i)
            if math.isnan(left_val) or current_bar_val <= left_val:
                is_pivot = False
                break
        
        if is_pivot:
            # Check right bars
            for i in range(1, rightbars + 1):
                # For pivot high, we need to look at future bars relative to the potential pivot bar.
                # In a real-time system, this would mean waiting for 'rightbars' bars to pass.
                # In a backtesting context, we can access future data.
                # Here, we assume 'source' contains all historical data up to the current bar_index.
                # To simulate Pine Script's behavior, we need to check bars *after* the current bar.
                # This is a simplification for the emulator.
                future_idx = self.bar_index + i
                if future_idx >= len(source): # Not enough future bars
                    is_pivot = False
                    break
                right_val = source[future_idx]
                if math.isnan(right_val) or current_bar_val <= right_val:
                    is_pivot = False
                    break
        
        return current_bar_val if is_pivot else float('nan')

    def ta_pivotlow(self, source, leftbars, rightbars):
        # Pivot low detection
        # source is expected to be a list (e.g., self.low)
        if not isinstance(source, list) or self.bar_index < leftbars + rightbars:
            return float('nan')

        current_bar_val = self.get_series_value(source, 0)
        if math.isnan(current_bar_val):
            return float('nan')

        is_pivot = True
        # Check left bars
        for i in range(1, leftbars + 1):
            left_val = self.get_series_value(source, i)
            if math.isnan(left_val) or current_bar_val >= left_val:
                is_pivot = False
                break
        
        if is_pivot:
            # Check right bars
            for i in range(1, rightbars + 1):
                future_idx = self.bar_index + i
                if future_idx >= len(source): # Not enough future bars
                    is_pivot = False
                    break
                right_val = source[future_idx]
                if math.isnan(right_val) or current_bar_val >= right_val:
                    is_pivot = False
                    break
        
        return current_bar_val if is_pivot else float('nan')

    def request_security(self, tickerid, timeframe_str, expression, lookahead=None):
        # In a real trading environment, this function would fetch data for the specified
        # ticker and timeframe, and then align it with the current chart's data.
        # For this emulator, we'll simulate this by returning the current series
        # if the timeframe matches, otherwise return NaN values.
        
        current_timeframe_period = self.timeframe_period()
        
        if timeframe_str == current_timeframe_period:
            if isinstance(expression, list):
                # If expression is a list of series (e.g., [pine.high, pine.low])
                # return the full historical series for each
                return [s for s in expression]
            else:
                # If expression is a single series, return its full historical series
                return expression
        else:
            # For different timeframes, return NaN values as a placeholder series.
            # A full implementation would involve loading and aligning actual HTF/LTF data.
            if isinstance(expression, list):
                # Return a list of NaN series, one for each series in the expression
                return [[float('nan')] * (self.bar_index + 1) for _ in expression]
            else:
                # Return a single NaN series
                return [float('nan')] * (self.bar_index + 1)

    def syminfo_tickerid(self):
        return "SYMBOL/TIMEFRAME" # In a real system, this would return the actual ticker ID

    def timeframe_period(self):
        return "1D" # In a real system, this would return the current chart's timeframe

    def timeframe_change(self, new_timeframe):
        return False

    def timeframe_in_seconds(self, tf):
        # Converts timeframe string to seconds for comparison
        if tf == '1S': return 1
        if tf == '1': return 60 # 1 minute
        if tf == '3': return 3 * 60 # 3 minutes
        if tf == '5': return 5 * 60 # 5 minutes
        if tf == '15': return 15 * 60 # 15 minutes
        if tf == '30': return 30 * 60 # 30 minutes
        if tf == '60': return 60 * 60 # 1 hour
        if tf == '120': return 2 * 60 * 60 # 2 hours
        if tf == '240': return 4 * 60 * 60 # 4 hours
        if tf == 'D': return 24 * 60 * 60 # 1 Day
        if tf == 'W': return 7 * 24 * 60 * 60 # 1 Week
        if tf == 'M': return 30 * 24 * 60 * 60 # 1 Month (approximation)
        return 60 # Default to 1 minute if not recognized

    def timeframe_isdaily(self): return False
    def timeframe_isweekly(self): return False
    def timeframe_ismonthly(self): return False

    def timestamp(self, tz_str, year, month, day, hour, minute):
        try:
            tz = pytz.timezone(tz_str)
            dt = datetime.datetime(year, month, day, hour, minute, tzinfo=tz)
            return int(dt.timestamp() * 1000) # Milliseconds
        except Exception as e:
            print(f"Error creating timestamp: {e}")
            return 0

    def barstate_isfirst(self): return self.bar_index == 0
    def barstate_islastconfirmedhistory(self): 
        # In a real backtesting environment, this would be true for the last bar of historical data.
        # For this emulator, we'll assume it's always true for now to allow alerts to fire.
        return True 
    def barstate_islast(self): 
        # In a real-time environment, this would be true for the very last bar.
        # For this emulator, we'll assume it's always true for now.
        return True 
    def barstate_isrealtime(self): 
        # In a real-time environment, this would be true for real-time bars.
        # For this emulator, we'll assume it's always false as we're processing historical data.
        return False 

    def plotcandle(self, open_val, high_val, low_val, close_val, color, wickcolor, bordercolor, title=''):
        global candles_to_draw
        candles_to_draw.append({'open': open_val, 'high': high_val, 'low': low_val, 'close': close_val, 'color': color, 'title': title, 'bar_index': self.bar_index})

    def alert(self, message, freq):
        print(f"ALERT: {message}")

    def alertcondition(self, condition, title, message):
        if condition:
            print(f"ALERT CONDITION MET: {title} - {message}")

    class ChartPoint:
        def __init__(self, time_val, na_val, price_val):
            self.time = time_val
            self.price = price_val

    class Label:
        def __init__(self, time_val=float('nan'), price_val=float('nan'), text='', xloc='xloc.bar_time', color=float('nan'), textcolor=float('nan'), style='label.style_label_left', size='size.normal'):
            self.time = time_val
            self.price = price_val
            self.text = text
            self.xloc = xloc
            self.color = color
            self.textcolor = textcolor
            self.style = style
            self.size = size
            self.id = id(self)

        def new(self, time_val=float('nan'), price_val=float('nan'), text='', xloc='xloc.bar_time', color=float('nan'), textcolor=float('nan'), style='label.style_label_left', size='size.normal'):
            new_label = PineScriptEmulator.Label(time_val, price_val, text, xloc, color, textcolor, style, size)
            global labels_to_draw
            labels_to_draw.append(new_label)
            return new_label

        def delete(self):
            global labels_to_draw
            labels_to_draw = [lbl for lbl in labels_to_draw if lbl.id != self.id]

        def set_point(self, point):
            self.time = point.time
            self.price = point.price

        def set_text(self, text):
            self.text = text

        style_label_up = "label.style_label_up"
        style_label_down = "label.style_label_down"
        style_label_left = "label.style_label_left"
        style_label_right = "label.style_label_right"

    class Box:
        def __init__(self, left=float('nan'), top=float('nan'), right=float('nan'), bottom=float('nan'), xloc='xloc.bar_time', bgcolor=float('nan'), border_color=float('nan'), border_style='line.style_solid', border_width=1):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.xloc = xloc
            self.bgcolor = bgcolor
            self.border_color = border_color
            self.border_style = border_style
            self.border_width = border_width
            self.id = id(self)

        def new(self, left=float('nan'), top=float('nan'), right=float('nan'), bottom=float('nan'), xloc='xloc.bar_time', bgcolor=float('nan'), border_color=float('nan'), border_style='line.style_solid', border_width=1):
            new_box = PineScriptEmulator.Box(left, top, right, bottom, xloc, bgcolor, border_color, border_style, border_width)
            global boxes_to_draw
            boxes_to_draw.append(new_box)
            return new_box

        def delete(self):
            global boxes_to_draw
            boxes_to_draw = [bx for bx in boxes_to_draw if bx.id != self.id]

        def set_left(self, val): self.left = val
        def set_top(self, val): self.top = val
        def set_right(self, val): self.right = val
        def set_bottom(self, val): self.bottom = val
        def set_bgcolor(self, val): self.bgcolor = val
        def set_border_color(self, val): self.border_color = val
        def set_border_style(self, val): self.border_style = val
        def set_border_width(self, val): self.border_width = val

    class Line:
        def __init__(self, x1=float('nan'), y1=float('nan'), x2=float('nan'), y2=float('nan'), xloc='xloc.bar_time', color=float('nan'), style='line.style_solid', width=1):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2
            self.xloc = xloc
            self.color = color
            self.style = style
            self.width = width
            self.id = id(self)

        def new(self, x1=float('nan'), y1=float('nan'), x2=float('nan'), y2=float('nan'), xloc='xloc.bar_time', color=float('nan'), style='line.style_solid', width=1):
            new_line = PineScriptEmulator.Line(x1, y1, x2, y2, xloc, color, style, width)
            global lines_to_draw
            lines_to_draw.append(new_line)
            return new_line

        def delete(self):
            global lines_to_draw
            lines_to_draw = [ln for ln in lines_to_draw if ln.id != self.id]

        def set_first_point(self, point):
            self.x1 = point.time
            self.y1 = point.price

        def set_second_point(self, point):
            self.x2 = point.time
            self.y2 = point.price

        style_solid = "line.style_solid"
        style_dashed = "line.style_dashed"
        style_dotted = "line.style_dotted"

    class Strategy:
        def __init__(self):
            pass
        def entry(self, id, direction, comment=''):
            print(f"STRATEGY ENTRY: ID={id}, Direction={direction}, Comment='{comment}'")
        def exit(self, id, from_entry, stop=None, limit=None):
            print(f"STRATEGY EXIT: ID={id}, From={from_entry}, Stop={stop}, Limit={limit}")
        long = "long"
        short = "short"
        class Commission:
            percent = "percent"
    
    # Initialize Pine Script emulator
    ta = None
    math = None
    syminfo = None
    timeframe = None
    barstate = None
    chart = None
    label = None
    box = None
    line = None
    strategy = None
    str = None # For string formatting

    def init_globals(self):
        self.ta = self
        self.math = self.Math()
        self.syminfo = self
        self.timeframe = self
        self.barstate = self
        self.chart = self.Chart()
        self.label = self.Label()
        self.box = self.Box()
        self.line = self.Line()
        self.strategy = self.Strategy()
        self.str = self.StringFormatter()

    class Math:
        def max(self, a, b): return max(a, b)
        def min(self, a, b): return min(a, b)
        def round(self, x): return round(x)
        def sqrt(self, x): return math.sqrt(x)
        def abs(self, x): return abs(x)
        def avg(self, a, b): return (a + b) / 2

    class Chart:
        def __init__(self):
            self.point = PineScriptEmulator.ChartPoint

    class StringFormatter:
        def format(self, format_string, *args):
            return format_string.format(*args)

    def array_binary_search_rightmost(self, arr, value):
        # Emulates Pine Script's array.binary_search_rightmost
        # Returns the index of the rightmost element equal to 'value', or -1 if not found.
        # If 'value' is not found, it returns the index of the first element smaller than 'value'.
        # If all elements are greater than 'value', it returns -1.
        
        if not isinstance(arr, list) or not arr:
            return -1

        low = 0
        high = len(arr) - 1
        result_idx = -1

        while low <= high:
            mid = (low + high) // 2
            if arr[mid] <= value:
                result_idx = mid
                low = mid + 1
            else:
                high = mid - 1
        return result_idx

# Initialize the emulator
pine = PineScriptEmulator()
pine.init_globals()

# Use pine.ta, pine.math, etc. for Pine Script built-in functions
ta = pine.ta
math = pine.math
syminfo = pine.syminfo
timeframe = pine.timeframe
barstate = pine.barstate
chart = pine.chart
label = pine.label
box = pine.box
line = pine.line
strategy = pine.strategy
str = pine.str

# Pine Script specific variables that need to be globally accessible or passed
# These are now accessed via the pine emulator instance (e.g., pine.open, pine.high)
last_bar_time = 0 # Last bar's timestamp, still needed for some calculations

# Constants
BULLISH_LEG = 1
BEARISH_LEG = 0

BULLISH = +1
BEARISH = -1

GREEN = '#4a7c59'
RED = '#8b5a5a'
BLUE = '#2157f3'
GRAY = '#878b94'
MONO_BULLISH = '#b2b5be'
MONO_BEARISH = '#5d606b'

HISTORICAL = 'Historical'
PRESENT = 'Present'

COLORED = 'Colored'
MONOCHROME = 'Monochrome'

ALL = 'All'
BOS = 'BOS'
CHOCH = 'CHoCH'

# Pine Script `size` enum
class Size:
    tiny = 'size.tiny'
    small = 'size.small'
    normal = 'size.normal'
size = Size()

ATR = 'Atr'
RANGE = 'Cumulative Mean Range'

CLOSE = 'Close'
HIGHLOW = 'High/Low'

SOLID = '⎯⎯⎯'
DASHED = '----'
DOTTED = '····'

SMART_GROUP = 'Smart Money Concepts'
SIGNAL_GROUP = 'Signal Generation'
TREND_GROUP = 'EMA Trend Signal'
INTERNAL_GROUP = 'Real Time Internal Structure'
SWING_GROUP = 'Real Time Swing Structure'
BLOCKS_GROUP = 'Order Blocks'
EQUAL_GROUP = 'EQH/EQL'
GAPS_GROUP = 'Fair Value Gaps'
LEVELS_GROUP = 'Highs & Lows MTF'
ZONES_GROUP = 'Premium & Discount Zones'
SESSION_GROUP = 'Session Management'
LIQUIDITY_GROUP = 'Liquidity & Sweeps'

ANALYSIS = 'Analysis'
SIGNAL = 'Signal'
OPEN = 'Open'
WIN = 'Win'
LOSS = 'Loss'

# Input Variables (using default values from Pine Script)
# Signal Generation Inputs
enableBuySignals  = True
enableSellSignals = True

# Session Management Inputs
tz = "Europe/Bratislava"
morning_start_h = 6
morning_start_m = 0
morning_end_h   = 10
morning_end_m   = 0
morning_color   = '#ffb74d' # color.new(#ffb74d, 80) - transparency handled in drawing
morning_name    = "Morning"

afternoon_start_h = 13
afternoon_start_m = 0
afternoon_end_h   = 16
afternoon_end_m   = 0
afternoon_color   = '#81c784' # color.new(#81c784, 80)
afternoon_name    = "Afternoon"

show_open_close    = True

# EMA Trend Inputs
showEmaInput = True
emaUseCurrentRes = True
emaResCustom = '15'
emaLen = 20
emaType = 2 # 1=SMA, 2=EMA, 3=WMA, 4=Hull, 5=VWMA, 6=RMA, 7=TEMA, 8=T3
emaFactorT3 = 0.7
emaColorDirection = True
emaLineWidth = 4

# Higher Timeframe EMA Inputs
showEmaHtfInput = True
emaHtfResCustom = '240' # 4 hours
emaHtfLen = 20
emaHtfType = 2
emaHtfFactorT3 = 0.7
emaHtfColorDirection = True
emaHtfLineWidth = 2

# Liquidity & Sweeps Inputs
showLiquiditySweepsInput = True
sweepThresholdInput = 0.5
ltfTimeframeInput = '3'
htfTimeframeInput = '240'
showSweepLabelsInput = True
useLtfRefinementInput = True

modeInput = HISTORICAL
styleInput = COLORED
showTrendInput = False

showInternalsInput = True
showInternalBullInput = ALL
internalBullColorInput = GREEN
showInternalBearInput = ALL
internalBearColorInput = RED
internalFilterConfluenceInput = False
internalStructureSize = size.tiny

showStructureInput = True
showSwingBullInput = ALL
swingBullColorInput = GREEN
showSwingBearInput = ALL
swingBearColorInput = RED
swingStructureSize = size.small
showSwingsInput = False
swingsLengthInput = 50
showHighLowSwingsInput = True

showInternalOrderBlocksInput = True
internalOrderBlocksSizeInput = 5
showSwingOrderBlocksInput = False
swingOrderBlocksSizeInput = 5
orderBlockFilterInput = ATR
orderBlockMitigationInput = HIGHLOW
showBreakerBlocksInput = True
internalBullishOrderBlockColor = '#5a7a9e' # color.new(#5a7a9e, 85)
internalBearishOrderBlockColor = '#9e7a7a' # color.new(#9e7a7a, 85)
swingBullishOrderBlockColor = '#4a6a8e' # color.new(#4a6a8e, 85)
swingBearishOrderBlockColor = '#8e6a6a' # color.new(#8e6a6a, 85)
breakerBullishColor = '#5a8a5a' # color.new(#5a8a5a, 75)
breakerBearishColor = '#8a5a5a' # color.new(#8a5a5a, 75)
orderBlockExtensionBarsInput = 0

showEqualHighsLowsInput = True
equalHighsLowsLengthInput = 3
equalHighsLowsThresholdInput = 0.1
equalHighsLowsSizeInput = size.tiny

showFairValueGapsInput = False
fairValueGapsThresholdInput = True
fairValueGapsTimeframeInput = ''
fvgMitigationStyleInput = 'Multi-Level'
fairValueGapsBullColorInput = '#5a8a6a' # color.new(#5a8a6a, 75)
fairValueGapsBearColorInput = '#8a6a6a' # color.new(#8a6a6a, 75)
fairValueGapsExtendInput = 1

showDailyLevelsInput = False
dailyLevelsStyleInput = SOLID
dailyLevelsColorInput = BLUE
showWeeklyLevelsInput = False
weeklyLevelsStyleInput = SOLID
weeklyLevelsColorInput = BLUE
showMonthlyLevelsInput = False
monthlyLevelsStyleInput = SOLID
monthlyLevelsColorInput = BLUE

showPremiumDiscountZonesInput = False
showOteZonesInput = False
premiumZoneColorInput = RED
equilibriumZoneColorInput = GRAY
discountZoneColorInput = GREEN
oteZoneColorInput = '#2962ff' # color.new(#2962ff, 85)

# DATA STRUCTURES & VARIABLES
class Alerts:
    def __init__(self):
        self.internalBullishBOS = False
        self.internalBearishBOS = False
        self.internalBullishCHoCH = False
        self.internalBearishCHoCH = False
        self.swingBullishBOS = False
        self.swingBearishBOS = False
        self.swingBullishCHoCH = False
        self.swingBearishCHoCH = False
        self.internalBullishOrderBlock = False
        self.internalBearishOrderBlock = False
        self.swingBullishOrderBlock = False
        self.swingBearishOrderBlock = False
        self.equalHighs = False
        self.equalLows = False
        self.bullishFairValueGap = False
        self.bearishFairValueGap = False
        self.bullishSweep = False
        self.bearishSweep = False
        self.buySignal = False
        self.sellSignal = False
        self.morningSessionStart = False
        self.afternoonSessionStart = False

class TrailingExtremes:
    def __init__(self):
        self.top = float('nan')
        self.bottom = float('nan')
        self.barTime = 0
        self.barIndex = 0
        self.lastTopTime = 0
        self.lastBottomTime = 0

class FairValueGap:
    def __init__(self, top, bottom, bias, topBox, bottomBox):
        self.top = top
        self.bottom = bottom
        self.bias = bias
        self.topBox = topBox
        self.bottomBox = bottomBox
        self.mitigationLevel = 0

class Trend:
    def __init__(self, bias):
        self.bias = bias

class SessionState:
    def __init__(self, start_ts, end_ts, active, high, low, open_val, close_val, boxid, openLine, closeLine, nameLabel):
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.active = active
        self.high = high
        self.low = low
        self.open = open_val
        self.close = close_val
        self.boxid = boxid
        self.openLine = openLine
        self.closeLine = closeLine
        self.nameLabel = nameLabel

class EqualDisplay:
    def __init__(self):
        self.l_ine = None
        self.l_abel = None

class Pivot:
    def __init__(self, currentLevel, lastLevel, crossed, barTime, barIndex):
        self.currentLevel = currentLevel
        self.lastLevel = lastLevel
        self.crossed = crossed
        self.barTime = barTime
        self.barIndex = barIndex

class OrderBlock:
    def __init__(self, barHigh, barLow, barTime, bias):
        self.barHigh = barHigh
        self.barLow = barLow
        self.barTime = barTime
        self.bias = bias
        self.isBreaker = False

# Global Variables (initialized with Pine Script's 'na' equivalent or default values)
swingHigh = Pivot(float('nan'), float('nan'), False, 0, 0)
swingLow = Pivot(float('nan'), float('nan'), False, 0, 0)
internalHigh = Pivot(float('nan'), float('nan'), False, 0, 0)
internalLow = Pivot(float('nan'), float('nan'), False, 0, 0)
equalHigh = Pivot(float('nan'), float('nan'), False, 0, 0)
equalLow = Pivot(float('nan'), float('nan'), False, 0, 0)
swingTrend = Trend(0)
internalTrend = Trend(0)
equalHighDisplay = EqualDisplay()
equalLowDisplay = EqualDisplay()
fairValueGaps = [] # List of FairValueGap objects
parsedHighs = [] # List of floats
parsedLows = [] # List of floats
trailing = TrailingExtremes()
swingOrderBlocks = [] # List of OrderBlock objects
internalOrderBlocks = [] # List of OrderBlock objects
breakerBlocks = [] # List of OrderBlock objects
swingOrderBlocksBoxes = [] # List of Box objects
internalOrderBlocksBoxes = [] # List of Box objects
breakerBlocksBoxes = [] # List of Box objects

# Global drawing objects for `drawStructure`
current_structure_line = None
current_structure_label = None

# Global drawing objects for `drawHighLowSwings`
topLine_swing = None
bottomLine_swing = None
topLabel_swing = None
bottomLabel_swing = None

# Global drawing objects for `drawZone` (Premium/Discount/OTE)
premium_zone_label = None
premium_zone_box = None
equilibrium_zone_label = None
equilibrium_zone_box = None
discount_zone_label = None
discount_zone_box = None
ote_zone_label = None
ote_zone_box = None

# Global drawing objects for `drawLevels`
topLine_level = None
bottomLine_level = None
topLabel_level = None
bottomLabel_level = None

# @variable                        color for swing bullish structures
swingBullishColor = MONO_BULLISH if styleInput == MONOCHROME else swingBullColorInput
# @variable                        color for swing bearish structures
swingBearishColor = MONO_BEARISH if styleInput == MONOCHROME else swingBearColorInput
# @variable                        color for bullish fair value gaps
fairValueGapBullishColor = '#5a8a6a' if styleInput == MONOCHROME else fairValueGapsBullColorInput 
# @variable                        color for bearish fair value gaps
fairValueGapBearishColor = '#8a6a6a' if styleInput == MONOCHROME else fairValueGapsBearColorInput 
# @variable                        color for premium zone
premiumZoneColor = MONO_BEARISH if styleInput == MONOCHROME else premiumZoneColorInput
# @variable                        color for discount zone
discountZoneColor = MONO_BULLISH if styleInput == MONOCHROME else discountZoneColorInput

# @variable                        bar index on current script iteration
currentBarIndex = 0
# @variable                        bar index on last script iteration
lastBarIndex = 0
# @variable                        alerts in current bar
currentAlerts = Alerts()

# Lists to store drawing objects for conceptual visualization
labels_to_draw = []
boxes_to_draw = []
lines_to_draw = []
candles_to_draw = []

# EMA Trend Variables
emaTrend = Trend(0)
emaHtfTrend = Trend(0)

# @variable                        time at start of chart
initialTime = 0

# Session Management Variables
morning = SessionState(float('nan'), float('nan'), False, float('nan'), float('nan'), float('nan'), float('nan'), None, None, None, None)
afternoon = SessionState(float('nan'), float('nan'), False, float('nan'), float('nan'), float('nan'), float('nan'), None, None, None, None)

# Liquidity Variables
atrVal = 1.0 # Initialized to a dummy value, will be updated in loop
liquidityLevels = []

# HTF data for pivots/liquidity (placeholders) - moved to main_strategy_loop
htfHigh_series = []
htfLow_series = []
htfPivotHigh = float('nan')
htfPivotLow = float('nan')

# LTF data for OB refinement (placeholders) - moved to main_strategy_loop
ltfOpen_series = []
ltfHigh_series = []
ltfLow_series = []
ltfClose_series = []

# These will be updated per bar in the loop
# @variable                        source to use in bearish order blocks mitigation
bearishOrderBlockMitigationSource = float('nan')
# @variable                        source to use in bullish order blocks mitigation
bullishOrderBlockMitigationSource = float('nan')
# @variable                        default volatility measure
atrMeasure = ta.atr(200) # This will be updated per bar in the loop
# @variable                        parsed volatility measure by user settings
volatilityMeasure = float('nan') # This will be updated per bar in the loop

# Session Management Helper Functions
def sess_start_ts(h, m):
    # Assuming current year, month, day for timestamp creation
    current_time_ms = pine.get_series_value(pine.time, 0)
    if math.isnan(current_time_ms):
        return float('nan')
    current_date = datetime.datetime.fromtimestamp(current_time_ms / 1000, tz=pytz.utc)
    return pine.timestamp(tz, current_date.year, current_date.month, current_date.day, h, m)

def sess_end_ts(h, m):
    current_time_ms = pine.get_series_value(pine.time, 0)
    if math.isnan(current_time_ms):
        return float('nan')
    current_date = datetime.datetime.fromtimestamp(current_time_ms / 1000, tz=pytz.utc)
    return pine.timestamp(tz, current_date.year, current_date.month, current_date.day, h, m)

def fix_end(start, end):
    return end if end > start else end + 24*60*60*1000

# EMA Helper Functions
def emaGd(src_series, len_val, factor):
    ema1_series = ta.ema(src_series, len_val)
    ema2_series = ta.ema(ema1_series, len_val)
    
    gd_values = [float('nan')] * (pine.bar_index + 1)

    for i in range(pine.bar_index + 1):
        ema1_val = pine.get_series_value(ema1_series, pine.bar_index - i)
        ema2_val = pine.get_series_value(ema2_series, pine.bar_index - i)

        if not math.isnan(ema1_val) and not math.isnan(ema2_val):
            gd_values[i] = ema1_val * (1 + factor) - ema2_val * factor
        else:
            gd_values[i] = float('nan')
    return gd_values

def emaT3(src_series, len_val, factor):
    ema_gd1_series = emaGd(src_series, len_val, factor)
    ema_gd2_series = emaGd(ema_gd1_series, len_val, factor)
    ema_gd3_series = emaGd(ema_gd2_series, len_val, factor)
    return ema_gd3_series

# Update a session state object
def update_session(s, start_ts, end_ts, bgc, name):
    # Access current bar data from pine emulator
    current_time = pine.get_series_value(pine.time, 0)
    current_open = pine.get_series_value(pine.open, 0)
    current_high = pine.get_series_value(pine.high, 0)
    current_low = pine.get_series_value(pine.low, 0)
    current_close = pine.get_series_value(pine.close, 0)
    current_time_close = pine.get_series_value(pine.time_close, 0)

    current_bar_in_session = current_time >= start_ts and current_time < end_ts
    prev_bar_in_session = pine.get_series_value(pine.time, 1) >= start_ts and pine.get_series_value(pine.time, 1) < end_ts if pine.bar_index > 0 else False

    bar_is_start = current_bar_in_session and not prev_bar_in_session
    bar_inside = current_bar_in_session
    bar_is_end = not current_bar_in_session and prev_bar_in_session

    if bar_inside and not s.active:
        s.active = True
        s.start_ts = start_ts
        s.open = current_open
        s.high = current_high
        s.low = current_low

    if bar_is_start:
        s.start_ts = start_ts
        s.end_ts = end_ts
        s.active = True
        s.open = current_open
        s.high = current_high
        s.low = current_low
        s.close = current_close

    if s.active and (bar_inside or bar_is_start):
        if bar_is_start:
            s.high = current_high
            s.low = current_low
        else:
            s.high = math.max(s.high, current_high)
            s.low = math.min(s.low, current_low)
        s.close = current_close
        
        if s.boxid is not None:
            s.boxid.delete()
        s.boxid = box.new(s.start_ts, s.high, current_time_close, s.low, xloc='xloc.bar_time', bgcolor=bgc, border_color=bgc)

        if show_open_close:
            if s.openLine is not None:
                s.openLine.delete()
            if s.closeLine is not None:
                s.closeLine.delete()
            s.openLine = line.new(s.start_ts, s.open, current_time_close, s.open, xloc='xloc.bar_time', color='#FFFFFF', style=line.style_dashed)
            s.closeLine = line.new(s.start_ts, s.close, current_time_close, s.close, xloc='xloc.bar_time', color='#FFFFFF', style=line.style_dotted)

    if bar_is_end and s.active:
        s.active = False


# EMA Trend Calculations
emaSrc = pine.close # Use pine.close series
emaRes = timeframe.period() if emaUseCurrentRes else emaResCustom

# Helper function to calculate different EMA types
def calculate_ema_type(src_series, length, ema_type, factor_t3):
    if ema_type == 1: # SMA
        return ta.sma(src_series, length)
    elif ema_type == 2: # EMA
        return ta.ema(src_series, length)
    elif ema_type == 3: # WMA
        return ta.wma(src_series, length)
    elif ema_type == 4: # Hull MA
        return ta.hma(src_series, length)
    elif ema_type == 5: # VWMA
        return ta.vwma(src_series, length)
    elif ema_type == 6: # RMA
        return ta.rma(src_series, length)
    elif ema_type == 7: # TEMA
        # TEMA = 3 * EMA(src, len) - 3 * EMA(EMA(src, len), len) + EMA(EMA(EMA(src, len), len), len)
        ema1 = ta.ema(src_series, length)
        ema2 = ta.ema(ema1, length)
        ema3 = ta.ema(ema2, length)
        
        tema_values = [float('nan')] * (pine.bar_index + 1)
        for i in range(pine.bar_index + 1):
            val1 = pine.get_series_value(ema1, pine.bar_index - i)
            val2 = pine.get_series_value(ema2, pine.bar_index - i)
            val3 = pine.get_series_value(ema3, pine.bar_index - i)
            if not math.isnan(val1) and not math.isnan(val2) and not math.isnan(val3):
                tema_values[i] = 3 * val1 - 3 * val2 + val3
            else:
                tema_values[i] = float('nan')
        return tema_values
    elif ema_type == 8: # T3
        return emaT3(src_series, length, factor_t3)
    return [float('nan')] * (pine.bar_index + 1) # Default to NaN series

# USER-DEFINED FUNCTIONS
# @function            Get the value of the current leg, it can be 0 (bearish) or 1 (bullish)
# @returns             int
def leg(size_val):
    leg_val = 0
    # Use pine.high and pine.low series for ta.highest and ta.lowest
    newLegHigh = pine.get_series_value(pine.high, size_val) > ta.highest(pine.high, size_val)
    newLegLow = pine.get_series_value(pine.low, size_val) < ta.lowest(pine.low, size_val)
    
    if newLegHigh:
        leg_val = BEARISH_LEG
    elif newLegLow:
        leg_val = BULLISH_LEG
    return leg_val

# @function            Identify whether the current value is the start of a new leg (swing)
# @param leg           (int) Current leg value
# @returns             bool
def startOfNewLeg(leg_val):
    return ta.change(leg_val) != 0

# @function            Identify whether the current level is the start of a new bearish leg (swing)
# @param leg           (int) Current leg value
# @returns             bool
def startOfBearishLeg(leg_val):
    return ta.change(leg_val) == -1

# @function            Identify whether the current level is the start of a new bullish leg (swing)
# @param leg           (int) Current leg value
# @returns             bool
def startOfBullishLeg(leg_val):
    return ta.change(leg_val) == +1

# @function            create a new label
# @param labelTime     bar time coordinate
# @param labelPrice    price coordinate
# @param tag           text to display
# @param labelColor    text color
# @param labelStyle    label style
# @returns             label ID
def drawLabel(labelTime, labelPrice, tag, labelColor, labelStyle):
    global labels_to_draw
    labels_to_draw.append({'time': labelTime, 'price': labelPrice, 'tag': tag, 'color': labelColor, 'style': labelStyle, 'bar_index': pine.bar_index})

# @function            create a new line and label representing an EQH or EQL
# @param p_ivot        starting pivot
# @param level         price level of current pivot
# @param size          how many bars ago was the current pivot detected
# @param equalHigh     true for EQH, false for EQL
# @returns             label ID
def drawEqualHighLow(p_ivot, level, size_val, equalHigh_flag):
    e_qualDisplay = equalHighDisplay if equalHigh_flag else equalLowDisplay
    
    tag = 'EQL'
    equalColor = swingBullishColor
    labelStyle = label.style_label_up

    if equalHigh_flag:
        tag = 'EQH'
        equalColor = swingBearishColor
        labelStyle = label.style_label_down

    if modeInput == PRESENT: # Pine Script: if modeInput == PRESENT, delete existing labels/lines
        if e_qualDisplay.l_ine is not None:
            e_qualDisplay.l_ine.delete()
        if e_qualDisplay.l_abel is not None:
            e_qualDisplay.l_abel.delete()

    e_qualDisplay.l_ine = line.new(p_ivot.barTime, p_ivot.currentLevel, pine.get_series_value(pine.time, size_val), level, xloc='xloc.bar_time', color=equalColor, style=line.style_dotted)
    
    labelPosition = math.round(0.5 * (p_ivot.barIndex + pine.bar_index - size_val))
    e_qualDisplay.l_abel = label.new(pine.get_series_value(pine.time, labelPosition), level, tag, xloc='xloc.bar_time', color=float('nan'), textcolor=equalColor, style=labelStyle, size=equalHighsLowsSizeInput)

# @function            store current structure and trailing swing points, and also display swing points and equal highs/lows
# @param size          (int) structure size
# @param equalHighLow  (bool) true for displaying current highs/lows
# @param internal      (bool) true for getting internal structures
# @returns             label ID
def getCurrentStructure(size_val, equalHighLow_flag=False, internal_flag=False):
    global swingHigh, swingLow, internalHigh, internalLow, equalHigh, equalLow, trailing # Need to modify global variables
    currentLeg = leg(size_val)
    newPivot = startOfNewLeg(currentLeg)
    pivotLow_flag = startOfBullishLeg(currentLeg)
    pivotHigh_flag = startOfBearishLeg(currentLeg)

    if newPivot:
        if pivotLow_flag:
            p_ivot = equalLow if equalHighLow_flag else (internalLow if internal_flag else swingLow)

            current_low_at_size_val = pine.get_series_value(pine.low, size_val)
            if equalHighLow_flag and not math.isnan(p_ivot.currentLevel) and not math.isnan(current_low_at_size_val) and \
               math.abs(p_ivot.currentLevel - current_low_at_size_val) < equalHighsLowsThresholdInput * atrMeasure:
                drawEqualHighLow(p_ivot, current_low_at_size_val, size_val, False)

            p_ivot.lastLevel = p_ivot.currentLevel
            p_ivot.currentLevel = current_low_at_size_val
            p_ivot.crossed = False
            p_ivot.barTime = pine.get_series_value(pine.time, size_val)
            p_ivot.barIndex = pine.get_series_value(pine.bar_index, size_val)

            if not equalHighLow_flag and not internal_flag:
                trailing.bottom = p_ivot.currentLevel
                trailing.barTime = p_ivot.barTime
                trailing.barIndex = p_ivot.barIndex
                trailing.lastBottomTime = p_ivot.barTime

            if showSwingsInput and not internal_flag and not equalHighLow_flag:
                drawLabel(pine.get_series_value(pine.time, size_val), p_ivot.currentLevel, 'LL' if p_ivot.currentLevel < p_ivot.lastLevel else 'HL', swingBullishColor, label.style_label_up)
        else:
            p_ivot = equalHigh if equalHighLow_flag else (internalHigh if internal_flag else swingHigh)

            current_high_at_size_val = pine.get_series_value(pine.high, size_val)
            if equalHighLow_flag and not math.isnan(p_ivot.currentLevel) and not math.isnan(current_high_at_size_val) and \
               math.abs(p_ivot.currentLevel - current_high_at_size_val) < equalHighsLowsThresholdInput * atrMeasure:
                drawEqualHighLow(p_ivot, current_high_at_size_val, size_val, True)

            p_ivot.lastLevel = p_ivot.currentLevel
            p_ivot.currentLevel = current_high_at_size_val
            p_ivot.crossed = False
            p_ivot.barTime = pine.get_series_value(pine.time, size_val)
            p_ivot.barIndex = pine.get_series_value(pine.bar_index, size_val)

            if not equalHighLow_flag and not internal_flag:
                trailing.top = p_ivot.currentLevel
                trailing.barTime = p_ivot.barTime
                trailing.barIndex = p_ivot.barIndex
                trailing.lastTopTime = p_ivot.barTime

            if showSwingsInput and not internal_flag and not equalHighLow_flag:
                drawLabel(pine.get_series_value(pine.time, size_val), p_ivot.currentLevel, 'HH' if p_ivot.currentLevel > p_ivot.lastLevel else 'LH', swingBearishColor, label.style_label_down)

# @function                draw line and label representing a structure
# @param p_ivot            base pivot point
# @param tag               test to display
# @param structureColor    base color
# @param lineStyle         line style
# @param labelStyle        label style
# @param labelSize         text size
# @returns                 label ID
def drawStructure(p_ivot, tag, structureColor, lineStyle, labelStyle, labelSize):
    # Pine Script `var` equivalent for drawing objects
    # In Python, we'll manage these globally for now to simulate `var` behavior
    global current_structure_line, current_structure_label

    if modeInput == PRESENT:
        if current_structure_line is not None:
            current_structure_line.delete()
            current_structure_line = None
        if current_structure_label is not None:
            current_structure_label.delete()
            current_structure_label = None

    current_structure_line = line.new(p_ivot.barTime, p_ivot.currentLevel, pine.get_series_value(pine.time, 0), p_ivot.currentLevel, xloc='xloc.bar_time', color=structureColor, style=lineStyle)
    current_structure_label = label.new(pine.get_series_value(pine.time, 0), p_ivot.currentLevel, tag, xloc='xloc.bar_time', color=float('nan'), textcolor=structureColor, style=labelStyle, size=labelSize)

# @function            delete order blocks and detect breaker blocks
# @param internal      true for internal order blocks
# @returns             orderBlock ID
def deleteOrderBlocks(internal_flag=False):
    global internalOrderBlocks, swingOrderBlocks, breakerBlocks, currentAlerts # Need to modify global variables
    orderBlocks = internalOrderBlocks if internal_flag else swingOrderBlocks

    indices_to_remove = []
    current_close = pine.get_series_value(pine.close, 0)

    for index, eachOrderBlock in enumerate(orderBlocks):
        crossedOderBlock = False
        becameBreaker = False
        
        if bearishOrderBlockMitigationSource > eachOrderBlock.barHigh and eachOrderBlock.bias == BEARISH:
            crossedOderBlock = True
            if current_close < eachOrderBlock.barLow and showBreakerBlocksInput:
                becameBreaker = True
                eachOrderBlock.isBreaker = True
                eachOrderBlock.bias = BULLISH
                if len(breakerBlocks) < 50:
                    breakerBlocks.insert(0, eachOrderBlock)
            if internal_flag:
                currentAlerts.internalBearishOrderBlock = True
            else:
                currentAlerts.swingBearishOrderBlock = True
        elif bullishOrderBlockMitigationSource < eachOrderBlock.barLow and eachOrderBlock.bias == BULLISH:
            crossedOderBlock = True
            if current_close > eachOrderBlock.barHigh and showBreakerBlocksInput:
                becameBreaker = True
                eachOrderBlock.isBreaker = True
                eachOrderBlock.bias = BEARISH
                if len(breakerBlocks) < 50:
                    breakerBlocks.insert(0, eachOrderBlock)
            if internal_flag:
                currentAlerts.internalBullishOrderBlock = True
            else:
                currentAlerts.swingBullishOrderBlock = True
        if crossedOderBlock and not becameBreaker:
            indices_to_remove.append(index)
    
    # Remove in reverse order to avoid index issues
    for index in sorted(indices_to_remove, reverse=True):
        orderBlocks.pop(index)

# @function            fetch and store order blocks with optional LTF refinement
# @param p_ivot        base pivot point
# @param internal      true for internal order blocks
# @param bias          BULLISH or BEARISH
# @returns             void
def storeOrdeBlock(p_ivot, internal_flag=False, bias=0):
    global internalOrderBlocks, swingOrderBlocks # Need to modify global variables
    if (not internal_flag and showSwingOrderBlocksInput) or (internal_flag and showInternalOrderBlocksInput):

        a_rray = []
        parsedIndex = -1
        
        arraySize = len(parsedHighs)
        startIdx = max(0, pine.bar_index - arraySize)
        pivotArrayIdx = p_ivot.barIndex - startIdx
        currentArrayIdx = pine.bar_index - startIdx
        
        if pivotArrayIdx >= 0 and pivotArrayIdx < arraySize and currentArrayIdx <= arraySize:
            if bias == BEARISH:
                a_rray = parsedHighs[pivotArrayIdx:currentArrayIdx]
                if a_rray:
                    parsedIndex = pivotArrayIdx + a_rray.index(max(a_rray))
            else:
                a_rray = parsedLows[pivotArrayIdx:currentArrayIdx]
                if a_rray:
                    parsedIndex = pivotArrayIdx + a_rray.index(min(a_rray))
        
            obHigh = parsedHighs[parsedIndex] if parsedIndex != -1 else float('nan')
            obLow = parsedLows[parsedIndex] if parsedIndex != -1 else float('nan')
            
            if useLtfRefinementInput:
                current_ltf_close = pine.get_series_value(ltfClose_series, 0)
                current_ltf_open = pine.get_series_value(ltfOpen_series, 0)
                current_ltf_high = pine.get_series_value(ltfHigh_series, 0)
                current_ltf_low = pine.get_series_value(ltfLow_series, 0)

                if not math.isnan(current_ltf_close) and not math.isnan(current_ltf_open) and \
                   not math.isnan(current_ltf_high) and not math.isnan(current_ltf_low):
                    if bias == BEARISH:
                        if current_ltf_close > current_ltf_open:
                            obHigh = math.max(obHigh, current_ltf_high)
                            obLow = math.max(obLow, current_ltf_low)
                    else: # BULLISH
                        if current_ltf_close < current_ltf_open:
                            obHigh = math.min(obHigh, current_ltf_high)
                            obLow = math.min(obLow, current_ltf_low)

            o_rderBlock = OrderBlock(obHigh, obLow, pine.get_series_value(pine.time, parsedIndex) if parsedIndex != -1 else 0, bias)
            orderBlocks = internalOrderBlocks if internal_flag else swingOrderBlocks
            
            if len(orderBlocks) >= 100:
                orderBlocks.pop()
            orderBlocks.insert(0, o_rderBlock) # unshift

# @function            draw order blocks as boxes
# @param internal      true for internal order blocks
# @returns             void
def drawOrderBlocks(internal_flag=False):
    orderBlocks = internalOrderBlocks if internal_flag else swingOrderBlocks
    orderBlocksSize = len(orderBlocks)
    if orderBlocksSize > 0:
        maxOrderBlocks = internalOrderBlocksSizeInput if internal_flag else swingOrderBlocksSizeInput
        parsedOrdeBlocks = orderBlocks[0:min(maxOrderBlocks, orderBlocksSize)]
        b_oxes = internalOrderBlocksBoxes if internal_flag else swingOrderBlocksBoxes        
        boxEndTime = last_bar_time + (orderBlockExtensionBarsInput * (pine.get_series_value(pine.time, 0) - pine.get_series_value(pine.time, 1)))
        for index, eachOrderBlock in enumerate(parsedOrdeBlocks):
            orderBlockColor = (MONO_BEARISH if eachOrderBlock.bias == BEARISH else MONO_BULLISH) if styleInput == MONOCHROME else (internalBearishOrderBlockColor if internal_flag and eachOrderBlock.bias == BEARISH else (internalBullishOrderBlockColor if internal_flag and eachOrderBlock.bias == BULLISH else (swingBearishOrderBlockColor if eachOrderBlock.bias == BEARISH else swingBullishOrderBlockColor)))
            b_ox = b_oxes[index]
            b_ox.set_left(eachOrderBlock.barTime)
            b_ox.set_top(eachOrderBlock.barHigh)
            b_ox.set_right(boxEndTime)
            b_ox.set_bottom(eachOrderBlock.barLow)
            b_ox.set_bgcolor(orderBlockColor)
            b_ox.set_border_color(orderBlockColor)

# @function            draw breaker blocks as boxes
# @returns             void
def drawBreakerBlocks():
    breakerBlocksSize = len(breakerBlocks)
    if breakerBlocksSize > 0 and showBreakerBlocksInput:
        maxBreakers = min(10, breakerBlocksSize)
        parsedBreakers = breakerBlocks[0:maxBreakers]
        boxEndTime = last_bar_time + (orderBlockExtensionBarsInput * (pine.get_series_value(pine.time, 0) - pine.get_series_value(pine.time, 1)))
        for index, eachBreaker in enumerate(parsedBreakers):
            if index < len(breakerBlocksBoxes):
                breakerColor = breakerBullishColor if eachBreaker.bias == BULLISH else breakerBearishColor
                b_ox = breakerBlocksBoxes[index]
                b_ox.set_left(eachBreaker.barTime)
                b_ox.set_top(eachBreaker.barHigh)
                b_ox.set_right(boxEndTime)
                b_ox.set_bottom(eachBreaker.barLow)
                b_ox.set_bgcolor(breakerColor)
                b_ox.set_border_color(breakerColor)
                b_ox.set_border_style(line.style_dashed)
                b_ox.set_border_width(2)

# @function            detect and draw structures, also detect and store order blocks
# @param internal      true for internal structures or order blocks
# @returns             void
def displayStructure(internal_flag=False):
    global internalHigh, swingHigh, internalLow, swingLow, internalTrend, swingTrend, currentAlerts # Need to modify global variables
    bullishBar = True
    bearishBar = True

    if internalFilterConfluenceInput:
        current_open = pine.get_series_value(pine.open, 0)
        current_high = pine.get_series_value(pine.high, 0)
        current_low = pine.get_series_value(pine.low, 0)
        current_close = pine.get_series_value(pine.close, 0)
        bullishBar = (current_high - math.max(current_close, current_open)) > (math.min(current_close, current_open) - current_low)
        bearishBar = (current_high - math.max(current_close, current_open)) < (math.min(current_close, current_open) - current_low)
    
    p_ivot = internalHigh if internal_flag else swingHigh
    t_rend = internalTrend if internal_flag else swingTrend

    lineStyle = line.style_dashed if internal_flag else line.style_solid
    labelSize = internalStructureSize if internal_flag else swingStructureSize

    extraCondition = (internalHigh.currentLevel != swingHigh.currentLevel and bullishBar) if internal_flag else True
    bullishColor = MONO_BULLISH if styleInput == MONOCHROME else (internalBullColorInput if internal_flag else swingBullColorInput)

    current_close = pine.get_series_value(pine.close, 0)
    if ta.crossover(pine.close, [p_ivot.currentLevel] * (pine.bar_index + 1)) and not p_ivot.crossed and extraCondition: # Pass p_ivot.currentLevel as a series
        tag = CHOCH if t_rend.bias == BEARISH else BOS

        if internal_flag:
            currentAlerts.internalBullishCHoCH = (tag == CHOCH)
            currentAlerts.internalBullishBOS = (tag == BOS)
        else:
            currentAlerts.swingBullishCHoCH = (tag == CHOCH)
            currentAlerts.swingBullishBOS = (tag == BOS)

        p_ivot.crossed = True
        t_rend.bias = BULLISH

        displayCondition = (showInternalsInput and (showInternalBullInput == ALL or (showInternalBullInput == BOS and tag != CHOCH) or (showInternalBullInput == CHOCH and tag == CHOCH))) if internal_flag else (showStructureInput and (showSwingBullInput == ALL or (showSwingBullInput == BOS and tag != CHOCH) or (showSwingBullInput == CHOCH and tag == CHOCH)))

        if displayCondition:
            drawStructure(p_ivot, tag, bullishColor, lineStyle, label.style_label_down, labelSize)

        if (internal_flag and showInternalOrderBlocksInput) or (not internal_flag and showSwingOrderBlocksInput):
            storeOrdeBlock(p_ivot, internal_flag, BULLISH)

    p_ivot = internalLow if internal_flag else swingLow    
    extraCondition = (internalLow.currentLevel != swingLow.currentLevel and bearishBar) if internal_flag else True
    bearishColor = MONO_BEARISH if styleInput == MONOCHROME else (internalBearColorInput if internal_flag else swingBearColorInput)

    if ta.crossunder(pine.close, [p_ivot.currentLevel] * (pine.bar_index + 1)) and not p_ivot.crossed and extraCondition: # Pass p_ivot.currentLevel as a series
        tag = CHOCH if t_rend.bias == BULLISH else BOS

        if internal_flag:
            currentAlerts.internalBearishCHoCH = (tag == CHOCH)
            currentAlerts.internalBearishBOS = (tag == BOS)
        else:
            currentAlerts.swingBearishCHoCH = (tag == CHOCH)
            currentAlerts.swingBearishBOS = (tag == BOS)

        p_ivot.crossed = True
        t_rend.bias = BEARISH

        displayCondition = (showInternalsInput and (showInternalBearInput == ALL or (showInternalBearInput == BOS and tag != CHOCH) or (showInternalBearInput == CHOCH and tag == CHOCH))) if internal_flag else (showStructureInput and (showSwingBearInput == ALL or (showSwingBearInput == BOS and tag != CHOCH) or (showSwingBearInput == CHOCH and tag == CHOCH)))
        
        if displayCondition:
            drawStructure(p_ivot, tag, bearishColor, lineStyle, label.style_label_up, labelSize)

        if (internal_flag and showInternalOrderBlocksInput) or (not internal_flag and showSwingOrderBlocksInput):
            storeOrdeBlock(p_ivot, internal_flag, BEARISH)

# @function            draw one fair value gap box (each fair value gap has two boxes)
# @param leftTime      left time coordinate
# @param rightTime     right time coordinate
# @param topPrice      top price level
# @param bottomPrice   bottom price level
# @param boxColor      box color
# @returns             box ID
def fairValueGapBox(leftTime, rightTime, topPrice, bottomPrice, boxColor):
    extended_right_time = rightTime + fairValueGapsExtendInput * (pine.get_series_value(pine.time, 0) - pine.get_series_value(pine.time, 1))
    return box.new(leftTime, topPrice, extended_right_time, bottomPrice, xloc='xloc.bar_time', border_color=boxColor, bgcolor=boxColor)

# @function            delete or update fair value gaps with multi-level mitigation
# @returns             void
def deleteFairValueGaps():
    global fairValueGaps, currentAlerts # Need to modify global variables
    indices_to_remove = []
    for index, eachFairValueGap in enumerate(fairValueGaps):
        fvgRange = eachFairValueGap.top - eachFairValueGap.bottom
        shouldRemove = False
        current_low = pine.get_series_value(pine.low, 0)
        current_high = pine.get_series_value(pine.high, 0)
        
        if fvgMitigationStyleInput == 'Full':
            if (current_low < eachFairValueGap.bottom and eachFairValueGap.bias == BULLISH) or \
               (current_high > eachFairValueGap.top and eachFairValueGap.bias == BEARISH):
                eachFairValueGap.topBox.delete()
                eachFairValueGap.bottomBox.delete()
                shouldRemove = True
        else: # Multi-level mitigation tracking
            if eachFairValueGap.bias == BULLISH:
                penetration = eachFairValueGap.top - current_low
                fillPercent = penetration / fvgRange
                
                if fillPercent >= 1.0 and eachFairValueGap.mitigationLevel < 4:
                    eachFairValueGap.mitigationLevel = 4
                    eachFairValueGap.topBox.delete()
                    eachFairValueGap.bottomBox.delete()
                    shouldRemove = True
                elif fillPercent >= 0.75 and eachFairValueGap.mitigationLevel < 3:
                    eachFairValueGap.mitigationLevel = 3
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBullishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBullishColor)
                elif fillPercent >= 0.50 and eachFairValueGap.mitigationLevel < 2:
                    eachFairValueGap.mitigationLevel = 2
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBullishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBullishColor)
                elif fillPercent >= 0.25 and eachFairValueGap.mitigationLevel < 1:
                    eachFairValueGap.mitigationLevel = 1
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBullishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBullishColor)
            else: # BEARISH
                penetration = current_high - eachFairValueGap.bottom
                fillPercent = penetration / fvgRange
                
                if fillPercent >= 1.0 and eachFairValueGap.mitigationLevel < 4:
                    eachFairValueGap.mitigationLevel = 4
                    eachFairValueGap.topBox.delete()
                    eachFairValueGap.bottomBox.delete()
                    shouldRemove = True
                elif fillPercent >= 0.75 and eachFairValueGap.mitigationLevel < 3:
                    eachFairValueGap.mitigationLevel = 3
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBearishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBearishColor)
                elif fillPercent >= 0.50 and eachFairValueGap.mitigationLevel < 2:
                    eachFairValueGap.mitigationLevel = 2
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBearishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBearishColor)
                elif fillPercent >= 0.25 and eachFairValueGap.mitigationLevel < 1:
                    eachFairValueGap.mitigationLevel = 1
                    eachFairValueGap.topBox.set_bgcolor(fairValueGapBearishColor)
                    eachFairValueGap.bottomBox.set_bgcolor(fairValueGapBearishColor)
        
        if shouldRemove:
            indices_to_remove.append(index)
    
    for index in sorted(indices_to_remove, reverse=True):
        fairValueGaps.pop(index)

# @function            draw fair value gaps
# @returns             fairValueGap ID
def drawFairValueGaps():
    global fairValueGaps, currentAlerts # Need to modify global variables

    # Pine Script: [lastClose, lastOpen, lastTime, currentHigh, currentLow, currentTime, last2High, last2Low] = request.security(syminfo.tickerid, fairValueGapsTimeframeInput, [close[1], open[1], time[1], high[0], low[0], time[0], high[2], low[2]],lookahead = barmerge.lookahead_on)
    # The request_security now returns full series. We need to get the *current* values from these series.
    security_data = ta.request_security(syminfo.tickerid(), fairValueGapsTimeframeInput, [pine.close, pine.open, pine.time, pine.high, pine.low, pine.time, pine.high, pine.low])
    
    # Ensure security_data is a list of lists (series)
    if not isinstance(security_data, list) or not security_data or not isinstance(security_data[0], list):
        # If request_security returned a single NaN or an empty list, handle it
        return

    # Get the current bar's values from the security series
    lastClose_series = security_data[0]
    lastOpen_series = security_data[1]
    lastTime_series = security_data[2]
    currentHigh_series = security_data[3]
    currentLow_series = security_data[4]
    currentTime_series = security_data[5]
    last2High_series = security_data[6]
    last2Low_series = security_data[7]

    lastClose = pine.get_series_value(lastClose_series, 1)
    lastOpen = pine.get_series_value(lastOpen_series, 1)
    lastTime = pine.get_series_value(lastTime_series, 1)
    currentHigh = pine.get_series_value(currentHigh_series, 0)
    currentLow = pine.get_series_value(currentLow_series, 0)
    currentTime = pine.get_series_value(currentTime_series, 0)
    last2High = pine.get_series_value(last2High_series, 2)
    last2Low = pine.get_series_value(last2Low_series, 2)

    barDeltaPercent = (lastClose - lastOpen) / (lastOpen * 100) if lastOpen != 0 else 0
    newTimeframe = timeframe.change(fairValueGapsTimeframeInput)
    
    # ta.cum expects a series. If barDeltaPercent is a single value, create a series for it.
    # The Pine Script `ta.cum(math.abs(newTimeframe ? barDeltaPercent : 0))` implies a series of `barDeltaPercent` or `0.0`
    # We need to create a series for `barDeltaPercent` if `newTimeframe` is true, otherwise a series of `0.0`
    if newTimeframe:
        threshold_series_input = [math.abs(barDeltaPercent)] * (pine.bar_index + 1) # Create a series of current bar's delta
    else:
        threshold_series_input = [0.0] * (pine.bar_index + 1) # Create a series of zeros

    # Get the current cumulative sum from the series
    cumulative_sum_series = ta.cum(threshold_series_input)
    current_cumulative_sum = pine.get_series_value(cumulative_sum_series, 0)

    threshold = current_cumulative_sum / (pine.bar_index + 1) * 2 if fairValueGapsThresholdInput else 0

    bullishFairValueGap = currentLow > last2High and lastClose > last2High and barDeltaPercent > threshold and newTimeframe
    bearishFairValueGap = currentHigh < last2Low and lastClose < last2Low and -barDeltaPercent > threshold and newTimeframe

    if bullishFairValueGap:
        currentAlerts.bullishFairValueGap = True
        fairValueGaps.insert(0, FairValueGap(currentLow, last2High, BULLISH, fairValueGapBox(lastTime, currentTime, currentLow, math.avg(currentLow, last2High), fairValueGapBullishColor), fairValueGapBox(lastTime, currentTime, math.avg(currentLow, last2High), last2High, fairValueGapBullishColor)))
    if bearishFairValueGap:
        currentAlerts.bearishFairValueGap = True
        fairValueGaps.insert(0, FairValueGap(currentHigh, last2Low, BEARISH, fairValueGapBox(lastTime, currentTime, currentHigh, math.avg(currentHigh, last2Low), fairValueGapBearishColor), fairValueGapBox(lastTime, currentTime, math.avg(currentHigh, last2Low), last2Low, fairValueGapBearishColor)))

# @function            get line style from string
# @param style         line style
# @returns             string
def getStyle(style_str):
    if style_str == SOLID: return line.style_solid
    if style_str == DASHED: return line.style_dashed
    if style_str == DOTTED: return line.style_dotted
    return line.style_solid

# @function            draw MultiTimeFrame levels
# @param timeframe     base timeframe
# @param sameTimeframe true if chart timeframe is same as base timeframe
# @param style         line style
# @param levelColor    line and text color
# @returns             void
def drawLevels(timeframe_str, sameTimeframe, style_str, levelColor):
    global topLine_level, bottomLine_level, topLabel_level, bottomLabel_level

    # Pine Script: [topLevel, bottomLevel, leftTime, rightTime] = request.security(syminfo.tickerid, timeframe, [high[1], low[1], time[1], time],lookahead = barmerge.lookahead_on)
    security_data = ta.request_security(syminfo.tickerid(), timeframe_str, [pine.high, pine.low, pine.time, pine.time])
    
    # Ensure security_data is a list of lists (series)
    if not isinstance(security_data, list) or not security_data or not isinstance(security_data[0], list):
        # If request_security returned a single NaN or an empty list, handle it
        # Delete existing levels if they are not being drawn
        if topLine_level is not None: topLine_level.delete(); topLine_level = None
        if bottomLine_level is not None: bottomLine_level.delete(); bottomLine_level = None
        if topLabel_level is not None: topLabel_level.delete(); topLabel_level = None
        if bottomLabel_level is not None: bottomLabel_level.delete(); bottomLabel_level = None
        return

    topLevel_series = security_data[0]
    bottomLevel_series = security_data[1]
    leftTime_series = security_data[2]
    rightTime_series = security_data[3]

    topLevel = pine.get_series_value(topLevel_series, 1) # high[1]
    bottomLevel = pine.get_series_value(bottomLevel_series, 1) # low[1]
    leftTime = pine.get_series_value(leftTime_series, 1) # time[1]
    rightTime = pine.get_series_value(rightTime_series, 0) # time[0]

    parsedTop = pine.get_series_value(pine.high, 0) if sameTimeframe else topLevel
    parsedBottom = pine.get_series_value(pine.low, 0) if sameTimeframe else bottomLevel    

    parsedLeftTime = pine.get_series_value(pine.time, 0) if sameTimeframe else leftTime
    parsedRightTime = pine.get_series_value(pine.time, 0) if sameTimeframe else rightTime

    parsedTopTime = pine.get_series_value(pine.time, 0)
    parsedBottomTime = pine.get_series_value(pine.time, 0)

    if not sameTimeframe:
        leftIndex = pine.array_binary_search_rightmost(pine.times_raw, parsedLeftTime)
        rightIndex = pine.array_binary_search_rightmost(pine.times_raw, parsedRightTime)

        if leftIndex != -1 and rightIndex != -1 and leftIndex <= rightIndex:
            timeArray = pine.times_raw[leftIndex : rightIndex + 1]
            topArray = pine.highs_raw[leftIndex : rightIndex + 1]
            bottomArray = pine.lows_raw[leftIndex : rightIndex + 1]

            if len(timeArray) > 0:
                max_top = float('-inf')
                max_top_time = initialTime
                for idx, val in enumerate(topArray):
                    if not math.isnan(val) and val > max_top:
                        max_top = val
                        max_top_time = timeArray[idx]
                parsedTopTime = max_top_time

                min_bottom = float('inf')
                min_bottom_time = initialTime
                for idx, val in enumerate(bottomArray):
                    if not math.isnan(val) and val < min_bottom:
                        min_bottom = val
                        min_bottom_time = timeArray[idx]
                parsedBottomTime = min_bottom_time
            else:
                parsedTopTime = initialTime
                parsedBottomTime = initialTime
        else:
            parsedTopTime = initialTime
            parsedBottomTime = initialTime

    current_time_close = pine.get_series_value(pine.time_close, 0)

    # Check if levels should be shown based on inputs
    show_current_levels = False
    if timeframe_str == 'D' and showDailyLevelsInput:
        show_current_levels = True
    elif timeframe_str == 'W' and showWeeklyLevelsInput:
        show_current_levels = True
    elif timeframe_str == 'M' and showMonthlyLevelsInput:
        show_current_levels = True

    if show_current_levels:
        if topLine_level is None:
            topLine_level = line.new(parsedTopTime, parsedTop, current_time_close, parsedTop, xloc='xloc.bar_time', color=levelColor, style=getStyle(style_str))
            bottomLine_level = line.new(parsedBottomTime, parsedBottom, current_time_close, parsedBottom, xloc='xloc.bar_time', color=levelColor, style=getStyle(style_str))
            topLabel_level = label.new(current_time_close, parsedTop, str.format('P{}H', timeframe_str), xloc='xloc.bar_time', color=float('nan'), textcolor=levelColor, size=size.small, style=label.style_label_left)
            bottomLabel_level = label.new(current_time_close, parsedBottom, str.format('P{}L', timeframe_str), xloc='xloc.bar_time', color=float('nan'), textcolor=levelColor, size=size.small, style=label.style_label_left)
        else:
            topLine_level.set_first_point(chart.point.new(parsedTopTime, float('nan'), parsedTop))
            topLine_level.set_second_point(chart.point.new(current_time_close, float('nan'), parsedTop))
            topLabel_level.set_point(chart.point.new(current_time_close, float('nan'), parsedTop))
            topLabel_level.set_text(str.format('P{}H', timeframe_str))
            topLabel_level.textcolor = levelColor
            topLine_level.color = levelColor
            topLine_level.style = getStyle(style_str)

            bottomLine_level.set_first_point(chart.point.new(parsedBottomTime, float('nan'), parsedBottom))
            bottomLine_level.set_second_point(chart.point.new(current_time_close, float('nan'), parsedBottom))
            bottomLabel_level.set_point(chart.point.new(current_time_close, float('nan'), parsedBottom))
            bottomLabel_level.set_text(str.format('P{}L', timeframe_str))
            bottomLabel_level.textcolor = levelColor
            bottomLine_level.color = levelColor
            bottomLine_level.style = getStyle(style_str)
    else: # If levels are not shown, delete them if they exist
        if topLine_level is not None: topLine_level.delete(); topLine_level = None
        if bottomLine_level is not None: bottomLine_level.delete(); bottomLine_level = None
        if topLabel_level is not None: topLabel_level.delete(); topLabel_level = None
        if bottomLabel_level is not None: bottomLabel_level.delete(); bottomLabel_level = None

# @function            true if chart timeframe is higher than provided timeframe
# @param timeframe     timeframe to check
# @returns             bool
def higherTimeframe(timeframe_str):
    return timeframe.in_seconds(timeframe_str) > timeframe.in_seconds(timeframe.period())

# @function            update trailing swing points
# @returns             int
def updateTrailingExtremes():
    global trailing # Need to modify global variables
    current_high = pine.get_series_value(pine.high, 0)
    current_low = pine.get_series_value(pine.low, 0)
    current_time = pine.get_series_value(pine.time, 0)

    trailing.top = math.max(current_high, trailing.top)
    trailing.lastTopTime = current_time if trailing.top == current_high else trailing.lastTopTime
    trailing.bottom = math.min(current_low, trailing.bottom)
    trailing.lastBottomTime = current_time if trailing.bottom == current_low else trailing.lastBottomTime

# @function            draw trailing swing points
# @returns             void
def drawHighLowSwings():
    global topLine_swing, bottomLine_swing, topLabel_swing, bottomLabel_swing

    current_time = pine.get_series_value(pine.time, 0)
    current_time_close = pine.get_series_value(pine.time_close, 0)

    if topLine_swing is None: # First bar, create objects
        topLine_swing = line.new(trailing.lastTopTime, trailing.top, current_time_close, trailing.top, xloc='xloc.bar_time', color=swingBearishColor, style=line.style_solid)
        bottomLine_swing = line.new(trailing.lastBottomTime, trailing.bottom, current_time_close, trailing.bottom, xloc='xloc.bar_time', color=swingBullishColor, style=line.style_solid)
        topLabel_swing = label.new(current_time_close, trailing.top, '', xloc='xloc.bar_time', color=float('nan'), textcolor=swingBearishColor, style=label.style_label_down, size=size.tiny)
        bottomLabel_swing = label.new(current_time_close, trailing.bottom, '', xloc='xloc.bar_time', color=float('nan'), textcolor=swingBullishColor, style=label.style_label_up, size=size.tiny)
    else: # Subsequent bars, update properties
        topLine_swing.set_first_point(chart.point.new(trailing.lastTopTime, float('nan'), trailing.top))
        topLine_swing.set_second_point(chart.point.new(current_time_close, float('nan'), trailing.top))
        topLabel_swing.set_point(chart.point.new(current_time_close, float('nan'), trailing.top))

        bottomLine_swing.set_first_point(chart.point.new(trailing.lastBottomTime, float('nan'), trailing.bottom))
        bottomLine_swing.set_second_point(chart.point.new(current_time_close, float('nan'), trailing.bottom))
        bottomLabel_swing.set_point(chart.point.new(current_time_close, float('nan'), trailing.bottom))

    topLabel_swing.set_text('Strong High' if swingTrend.bias == BEARISH else 'Weak High')
    bottomLabel_swing.set_text('Strong Low' if swingTrend.bias == BULLISH else 'Weak Low')

# @function            draw a zone with a label and a box
# @param labelLevel    price level for label
# @param labelIndex    bar index for label
# @param top           top price level for box
# @param bottom        bottom price level for box
# @param tag           text to display
# @param zoneColor     base color
# @param style         label style
# @returns             void
def drawZone(label_obj, box_obj, labelLevel, labelIndex, top, bottom, tag, zoneColor, style_str):
    current_time = pine.get_series_value(pine.time, 0)
    current_time_close = pine.get_series_value(pine.time_close, 0)

    if box_obj is None:
        box_obj = box.new(current_time, top, current_time_close, bottom, xloc='xloc.bar_time', bgcolor=zoneColor, border_color=zoneColor)
    else:
        box_obj.set_left(current_time)
        box_obj.set_top(top)
        box_obj.set_right(current_time_close)
        box_obj.set_bottom(bottom)
        box_obj.set_bgcolor(zoneColor)
        box_obj.set_border_color(zoneColor)

    if label_obj is None:
        label_obj = label.new(current_time, labelLevel, tag, xloc='xloc.bar_time', color=float('nan'), textcolor=zoneColor, style=style_str, size=size.tiny)
    else:
        label_obj.set_point(chart.point.new(current_time, float('nan'), labelLevel))
        label_obj.set_text(tag)
        label_obj.textcolor = zoneColor
        label_obj.style = style_str
        label_obj.size = size.tiny
    return label_obj, box_obj

# @function            draw premium/discount zones with optional OTE
# @returns             void
def drawPremiumDiscountZones():
    global premium_zone_label, premium_zone_box, equilibrium_zone_label, equilibrium_zone_box, discount_zone_label, discount_zone_box, ote_zone_label, ote_zone_box

    priceRange = trailing.top - trailing.bottom
    
    if showPremiumDiscountZonesInput:
        # Premium Zone
        premium_zone_label, premium_zone_box = drawZone(premium_zone_label, premium_zone_box, trailing.top, math.round(0.5 * (trailing.barIndex + pine.bar_index)), trailing.top, 0.95 * trailing.top + 0.05 * trailing.bottom, 'Premium', premiumZoneColor, label.style_label_down)

        # Equilibrium Zone
        equilibriumLevel = math.avg(trailing.top, trailing.bottom)
        equilibrium_zone_label, equilibrium_zone_box = drawZone(equilibrium_zone_label, equilibrium_zone_box, equilibriumLevel, pine.bar_index, 0.525 * trailing.top + 0.475 * trailing.bottom, 0.525 * trailing.bottom + 0.475 * trailing.top, 'Equilibrium', equilibriumZoneColorInput, label.style_label_left)

        # Discount Zone
        discount_zone_label, discount_zone_box = drawZone(discount_zone_label, discount_zone_box, trailing.bottom, math.round(0.5 * (trailing.barIndex + pine.bar_index)), 0.95 * trailing.bottom + 0.05 * trailing.top, trailing.bottom, 'Discount', discountZoneColor, label.style_label_up)
        
        # OTE Zones (0.62-0.79 Fibonacci retracement)
        if showOteZonesInput:
            oteHigh = trailing.bottom + 0.79 * priceRange
            oteLow = trailing.bottom + 0.62 * priceRange
            ote_zone_label, ote_zone_box = drawZone(ote_zone_label, ote_zone_box, math.avg(oteHigh, oteLow), pine.bar_index, oteHigh, oteLow, 'OTE', oteZoneColorInput, label.style_label_left)
        else: # If OTE zones are not shown, delete them if they exist
            if ote_zone_label is not None:
                ote_zone_label.delete()
                ote_zone_label = None
            if ote_zone_box is not None:
                ote_zone_box.delete()
                ote_zone_box = None
    else: # If Premium/Discount Zones are not shown, delete all related objects
        if premium_zone_label is not None:
            premium_zone_label.delete()
            premium_zone_label = None
        if premium_zone_box is not None:
            premium_zone_box.delete()
            premium_zone_box = None
        if equilibrium_zone_label is not None:
            equilibrium_zone_label.delete()
            equilibrium_zone_label = None
        if equilibrium_zone_box is not None:
            equilibrium_zone_box.delete()
            equilibrium_zone_box = None
        if discount_zone_label is not None:
            discount_zone_label.delete()
            discount_zone_label = None
        if discount_zone_box is not None:
            discount_zone_box.delete()
            discount_zone_box = None
        if ote_zone_label is not None:
            ote_zone_label.delete()
            ote_zone_label = None
        if ote_zone_box is not None:
            ote_zone_box.delete()
            ote_zone_box = None

# @function            true if current price is in the discount zone
# @returns             bool
def inDiscountZone():
    current_close = pine.get_series_value(pine.close, 0)
    priceRange = trailing.top - trailing.bottom
    discountZoneTop = trailing.bottom + 0.05 * priceRange
    discountZoneBottom = trailing.bottom
    return current_close >= discountZoneBottom and current_close <= discountZoneTop

# @function            true if current price is in the premium zone
# @returns             bool
def inPremiumZone():
    current_close = pine.get_series_value(pine.close, 0)
    priceRange = trailing.top - trailing.bottom
    premiumZoneTop = trailing.top
    premiumZoneBottom = trailing.top - 0.05 * priceRange
    return current_close <= premiumZoneTop and current_close >= premiumZoneBottom

# @function            collect liquidity levels from sessions, EQH/EQL, FVG, HTF pivots
# @returns             void
def collectLiquidityLevels():
    global liquidityLevels # Need to modify global variables
    liquidityLevels.clear()
    if not math.isnan(morning.high):
        liquidityLevels.append(morning.high)
        liquidityLevels.append(morning.low)
    if not math.isnan(afternoon.high):
        liquidityLevels.append(afternoon.high)
        liquidityLevels.append(afternoon.low)
    if not math.isnan(equalHigh.currentLevel):
        liquidityLevels.append(equalHigh.currentLevel)
    if not math.isnan(equalLow.currentLevel):
        liquidityLevels.append(equalLow.currentLevel)
    if len(fairValueGaps) > 0:
        lastFVG = fairValueGaps[0]
        liquidityLevels.append(math.avg(lastFVG.top, lastFVG.bottom))
    if htfPivotHigh is not None and not math.isnan(htfPivotHigh):
        liquidityLevels.append(htfPivotHigh)
    if htfPivotLow is not None and not math.isnan(htfPivotLow):
        liquidityLevels.append(htfPivotLow)
    if not math.isnan(swingHigh.currentLevel):
        liquidityLevels.append(swingHigh.currentLevel)
    if not math.isnan(swingLow.currentLevel):
        liquidityLevels.append(swingLow.currentLevel)

# @function            detect liquidity sweeps (wick-through-and-reject logic)
# @returns             void
def detectSweeps():
    global currentAlerts # Need to modify global variables
    current_low = pine.get_series_value(pine.low, 0)
    current_high = pine.get_series_value(pine.high, 0)
    current_close = pine.get_series_value(pine.close, 0)
    current_bar_index = pine.bar_index

    if showLiquiditySweepsInput and len(liquidityLevels) > 0:
        for level in liquidityLevels:
            sweepDist = atrVal * sweepThresholdInput
            if current_low < level and current_low < level - sweepDist and current_close > level:
                currentAlerts.bullishSweep = True
                if showSweepLabelsInput:
                    drawLabel(current_bar_index, current_low, '↑ Sweep', GREEN, label.style_label_up)
            if current_high > level and current_high > level + sweepDist and current_close < level:
                currentAlerts.bearishSweep = True
                if showSweepLabelsInput:
                    drawLabel(current_bar_index, current_high, '↓ Sweep', RED, label.style_label_down)

# MUTABLE VARIABLES & EXECUTION (Main Loop - conceptual)
def main_strategy_loop(data_feed):
    global last_bar_time, currentBarIndex, lastBarIndex, atrVal, initialTime # Access global variables

    # Initialize drawing objects lists (moved from global scope to here for clarity)
    global labels_to_draw, boxes_to_draw, lines_to_draw, candles_to_draw
    labels_to_draw = []
    boxes_to_draw = []
    lines_to_draw = []
    candles_to_draw = []

    # Initialize order block boxes once at the start of the strategy loop
    if showSwingOrderBlocksInput:
        for index in range(swingOrderBlocksSizeInput):
            swingOrderBlocksBoxes.append(box.new(float('nan'), float('nan'), float('nan'), float('nan'), xloc='xloc.bar_time'))
    if showInternalOrderBlocksInput:
        for index in range(internalOrderBlocksSizeInput):
            internalOrderBlocksBoxes.append(box.new(float('nan'), float('nan'), float('nan'), float('nan'), xloc='xloc.bar_time'))
    if showBreakerBlocksInput:
        for index in range(10):
            breakerBlocksBoxes.append(box.new(float('nan'), float('nan'), float('nan'), float('nan'), xloc='xloc.bar_time'))

    for i, bar_data in enumerate(data_feed):
        # Update PineScriptEmulator's internal series data
        pine.bar_index = i
        pine.open.append(bar_data['open'])
        pine.high.append(bar_data['high'])
        pine.low.append(bar_data['low'])
        pine.close.append(bar_data['close'])
        pine.time.append(bar_data['time']) # Assuming timestamp in milliseconds
        pine.time_close.append(bar_data['time_close']) # Assuming timestamp of close in milliseconds
        
        # Initialize initialTime on the first bar
        if i == 0:
            initialTime = pine.get_series_value(pine.time, 0)

        # Store raw highs, lows, and times
        pine.highs_raw.append(bar_data['high'])
        pine.lows_raw.append(bar_data['low'])
        pine.times_raw.append(bar_data['time'])

        # Calculate True Range for the current bar and append to tr_series
        pine.tr_series.append(pine.ta_tr())

        # Update atrVal for current bar
        global atrVal
        atrVal = ta.atr(14) # Recalculate ATR using the emulator's ta_atr

        # Update volatilityMeasure for current bar
        global volatilityMeasure
        current_atr_measure = ta.atr(200)
        current_cum_tr = pine.get_series_value(ta.cum(pine.tr_series), 0)
        volatilityMeasure = current_atr_measure if orderBlockFilterInput == ATR else (current_cum_tr / (pine.bar_index + 1) if (pine.bar_index + 1) > 0 else float('nan'))

        # Update mitigation sources
        global bearishOrderBlockMitigationSource, bullishOrderBlockMitigationSource
        bearishOrderBlockMitigationSource = pine.get_series_value(pine.close, 0) if orderBlockMitigationInput == CLOSE else pine.get_series_value(pine.high, 0)
        bullishOrderBlockMitigationSource = pine.get_series_value(pine.close, 0) if orderBlockMitigationInput == CLOSE else pine.get_series_value(pine.low, 0)

        # Pine Script: highVolatilityBar = (high - low) >= (2 * volatilityMeasure)
        highVolatilityBar = (pine.get_series_value(pine.high, 0) - pine.get_series_value(pine.low, 0)) >= (2 * volatilityMeasure)
        # Pine Script: parsedHigh = highVolatilityBar ? low : high
        parsedHigh = pine.get_series_value(pine.low, 0) if highVolatilityBar else pine.get_series_value(pine.high, 0)
        # Pine Script: parsedLow = highVolatilityBar ? high : low
        parsedLow = pine.get_series_value(pine.high, 0) if highVolatilityBar else pine.get_series_value(pine.low, 0)

        # We store current values into the arrays at each bar with size limits
        if len(parsedHighs) > 5000:
            parsedHighs.pop(0)
            parsedLows.pop(0)
            pine.highs_raw.pop(0)
            pine.lows_raw.pop(0)
            pine.times_raw.pop(0)
        parsedHighs.append(parsedHigh)
        parsedLows.append(parsedLow)
        pine.highs_raw.append(bar_data['high'])
        pine.lows_raw.append(bar_data['low'])
        pine.times_raw.append(bar_data['time'])

        # HTF/LTF data for pivots/liquidity (conceptual)
        # In a real implementation, this would fetch data from a data provider
        # For now, request_security will return current timeframe data if timeframe matches, else NaN series
        htf_data = ta.request_security(syminfo.tickerid(), htfTimeframeInput, [pine.high, pine.low])
        htfHigh_series_current = htf_data[0] if isinstance(htf_data, list) else float('nan')
        htfLow_series_current = htf_data[1] if isinstance(htf_data, list) else float('nan')
        
        # Append current HTF values to series for pivot calculation
        htfHigh_series.append(htfHigh_series_current)
        htfLow_series.append(htfLow_series_current)

        # Calculate pivots using the series
        global htfPivotHigh, htfPivotLow
        htfPivotHigh = ta.pivothigh(htfHigh_series, 5, 5)
        htfPivotLow = ta.pivotlow(htfLow_series, 5, 5)

        ltf_data = ta.request_security(syminfo.tickerid(), ltfTimeframeInput, [pine.open, pine.high, pine.low, pine.close])
        ltfOpen_series_current = ltf_data[0] if isinstance(ltf_data, list) else float('nan')
        ltfHigh_series_current = ltf_data[1] if isinstance(ltf_data, list) else float('nan')
        ltfLow_series_current = ltf_data[2] if isinstance(ltf_data, list) else float('nan')
        ltfClose_series_current = ltf_data[3] if isinstance(ltf_data, list) else float('nan')

        # Append current LTF values to series for OB refinement
        ltfOpen_series.append(ltfOpen_series_current)
        ltfHigh_series.append(ltfHigh_series_current)
        ltfLow_series.append(ltfLow_series_current)
        ltfClose_series.append(ltfClose_series_current)

        # Calculate EMAs
        # Ensure emaSrc and emaHtfSrc always refer to the current pine.close series
        global emaSrc, emaHtfSrc
        emaSrc = pine.close
        emaHtfSrc = pine.close

        ema = calculate_ema_type(emaSrc, emaLen, emaType, emaFactorT3)
        current_ema = pine.get_series_value(ema, 0)
        prev_ema = pine.get_series_value(ema, 1)

        global ema_up, ema_down
        if not math.isnan(current_ema) and not math.isnan(prev_ema):
            ema_up = current_ema > prev_ema
            ema_down = current_ema < prev_ema
            if ema_up:
                emaTrend.bias = BULLISH
            elif ema_down:
                emaTrend.bias = BEARISH
            else:
                emaTrend.bias = 0 # Neutral
        else:
            ema_up = False
            ema_down = False
            emaTrend.bias = 0

        emaHtf = calculate_ema_type(emaHtfSrc, emaHtfLen, emaHtfType, emaHtfFactorT3)
        current_emaHtf = pine.get_series_value(emaHtf, 0)
        prev_emaHtf = pine.get_series_value(emaHtf, 1)

        global emaHtf_up, emaHtf_down
        if not math.isnan(current_emaHtf) and not math.isnan(prev_emaHtf):
            emaHtf_up = current_emaHtf > prev_emaHtf
            emaHtf_down = current_emaHtf < prev_emaHtf
            if emaHtf_up:
                emaHtfTrend.bias = BULLISH
            elif emaHtf_down:
                emaHtfTrend.bias = BEARISH
            else:
                emaHtfTrend.bias = 0 # Neutral
        else:
            emaHtf_up = False
            emaHtf_down = False
            emaHtfTrend.bias = 0

        # Pine Script: parsedOpen = showTrendInput ? open : na
        parsedOpen = pine.get_series_value(pine.open, 0) if showTrendInput else float('nan')
        # Pine Script: candleColor = internalTrend.bias == BULLISH ? swingBullishColor : swingBearishColor
        candleColor = swingBullishColor if internalTrend.bias == BULLISH else swingBearishColor
        # Pine Script: plotcandle(parsedOpen,high,low,close,color = candleColor, wickcolor = candleColor, bordercolor = candleColor)
        ta.plotcandle(parsedOpen, pine.get_series_value(pine.high, 0), pine.get_series_value(pine.low, 0), pine.get_series_value(pine.close, 0), color=candleColor, wickcolor=candleColor, bordercolor=candleColor, title='Candle Trend')

        # Plot EMA
        emaTrendColor = (GREEN if ema_up else RED) if emaColorDirection else BLUE
        if showEmaInput and not math.isnan(current_ema):
            # In Pine Script, plot() creates a series. Here we're just conceptually plotting the current value.
            # For actual plotting, you'd store these values and render them later.
            pass # Plotting is conceptual in this emulator

        # Plot Higher Timeframe EMA
        emaHtfTrendColor = (GREEN if emaHtf_up else RED) if emaHtfColorDirection else BLUE
        if showEmaHtfInput and not math.isnan(current_emaHtf):
            # Conceptual plotting
            pass # Plotting is conceptual in this emulator

        # Session Management
        morning_start = sess_start_ts(morning_start_h, morning_start_m)
        morning_end   = fix_end(morning_start, sess_end_ts(morning_end_h, morning_end_m))
        afternoon_start = sess_start_ts(afternoon_start_h, afternoon_start_m)
        afternoon_end   = fix_end(afternoon_start, sess_end_ts(afternoon_end_h, afternoon_end_m))

        update_session(morning, morning_start, morning_end, morning_color, morning_name)
        update_session(afternoon, afternoon_start, afternoon_end, afternoon_color, afternoon_name)

        if showHighLowSwingsInput or showPremiumDiscountZonesInput:
            updateTrailingExtremes()

            if showHighLowSwingsInput:
                drawHighLowSwings()

            if showPremiumDiscountZonesInput:
                drawPremiumDiscountZones()

        # Liquidity Execution
        collectLiquidityLevels()
        detectSweeps()

        # Structure Detection and Order Blocks
        if showFairValueGapsInput:
            deleteFairValueGaps()

        getCurrentStructure(swingsLengthInput, False)
        getCurrentStructure(5, False, True)

        if showEqualHighsLowsInput:
            getCurrentStructure(equalHighsLowsLengthInput, True)

        if showInternalsInput or showInternalOrderBlocksInput or showTrendInput:
            displayStructure(True)

        if showStructureInput or showSwingOrderBlocksInput or showHighLowSwingsInput:
            displayStructure()

        if showInternalOrderBlocksInput:
            deleteOrderBlocks(True)

        if showSwingOrderBlocksInput:
            deleteOrderBlocks()

        # Fair Value Gaps
        if showFairValueGapsInput:
            drawFairValueGaps()

        # MTF Levels
        lastBarIndex = currentBarIndex
        currentBarIndex = pine.bar_index
        newBar = currentBarIndex != lastBarIndex

        if barstate.islastconfirmedhistory() or (barstate.isrealtime() and newBar):
            if showDailyLevelsInput and not higherTimeframe('D'):
                drawLevels('D', timeframe.isdaily(), dailyLevelsStyleInput, dailyLevelsColorInput)

            if showWeeklyLevelsInput and not higherTimeframe('W'):
                drawLevels('W', timeframe.isweekly(), weeklyLevelsStyleInput, weeklyLevelsColorInput)

            if showMonthlyLevelsInput and not higherTimeframe('M'):
                drawLevels('M', timeframe.ismonthly(), monthlyLevelsStyleInput, monthlyLevelsColorInput)

        # Strategy Entry/Exit Logic (EMA-only for testing)
        takeProfit = float('nan')
        stopLoss = float('nan')

        # Buy when EMA turns up and Higher Timeframe EMA is bullish
        # ema_up and ema_down are already boolean values, no need to get_series_value on them
        if enableBuySignals and ema_up and (pine.bar_index == 0 or not pine.get_series_value([ema_up], 1)) and emaHtfTrend.bias == BULLISH:
            strategy.entry('Buy', strategy.long, comment='EMA Buy Signal')
            current_close = pine.get_series_value(pine.close, 0)
            takeProfit = current_close + (atrVal * 2) # 2x ATR Take Profit
            stopLoss = current_close - (atrVal * 1)   # 1x ATR Stop Loss
            strategy.exit('Exit Buy', from_entry='Buy', stop=stopLoss, limit=takeProfit)
            currentAlerts.buySignal = True # Set alert condition

        # Sell when EMA turns down and Higher Timeframe EMA is bearish
        if enableSellSignals and ema_down and (pine.bar_index == 0 or not pine.get_series_value([ema_down], 1)) and emaHtfTrend.bias == BEARISH:
            strategy.entry('Sell', strategy.short, comment='EMA Sell Signal')
            current_close = pine.get_series_value(pine.close, 0)
            takeProfit = current_close - (atrVal * 2) # 2x ATR Take Profit
            stopLoss = current_close + (atrVal * 1)   # 1x ATR Stop Loss
            strategy.exit('Exit Sell', from_entry='Sell', stop=stopLoss, limit=takeProfit)
            currentAlerts.sellSignal = True # Set alert condition

        # Draw Order Blocks and Breaker Blocks
        # These should be called every bar, not just at the end of history
        if showInternalOrderBlocksInput:        
            drawOrderBlocks(True)
        if showSwingOrderBlocksInput:        
            drawOrderBlocks()
        if showBreakerBlocksInput:
            drawBreakerBlocks()

        # ALERTS
        # One-time test alert
        if barstate.islastconfirmedhistory():
            ta.alert("Pine Script emulation is running and alerts are active!", "alert.freq_once_per_bar_close")

        ta.alertcondition(currentAlerts.internalBullishBOS,        'Internal Bullish BOS',         'Internal Bullish BOS formed')
        ta.alertcondition(currentAlerts.internalBullishCHoCH,      'Internal Bullish CHoCH',       'Internal Bullish CHoCH formed')
        ta.alertcondition(currentAlerts.internalBearishBOS,        'Internal Bearish BOS',         'Internal Bearish BOS formed')
        ta.alertcondition(currentAlerts.internalBearishCHoCH,      'Internal Bearish CHoCH',       'Internal Bearish CHoCH formed')

        ta.alertcondition(currentAlerts.swingBullishBOS,           'Bullish BOS',                  'Bullish BOS formed')
        ta.alertcondition(currentAlerts.swingBullishCHoCH,         'Bullish CHoCH',                'Bullish CHoCH formed')
        ta.alertcondition(currentAlerts.swingBearishBOS,           'Bearish BOS',                  'Bearish BOS formed')
        ta.alertcondition(currentAlerts.swingBearishCHoCH,         'Bearish CHoCH',                'Bearish CHoCH formed')

        ta.alertcondition(currentAlerts.internalBullishOrderBlock, 'Bullish Internal OB Breakout', 'Price broke bullish internal OB')
        ta.alertcondition(currentAlerts.internalBearishOrderBlock, 'Bearish Internal OB Breakout', 'Price broke bearish internal OB')
        ta.alertcondition(currentAlerts.swingBullishOrderBlock,    'Bullish Swing OB Breakout',    'Price broke bullish swing OB')
        ta.alertcondition(currentAlerts.swingBearishOrderBlock,    'Bearish Swing OB Breakout',    'Price broke bearish swing OB')

        ta.alertcondition(currentAlerts.equalHighs,                'Equal Highs',                  'Equal highs detected')
        ta.alertcondition(currentAlerts.equalLows,                 'Equal Lows',                   'Equal lows detected')

        ta.alertcondition(currentAlerts.bullishFairValueGap,       'Bullish FVG',                  'Bullish FVG formed')
        ta.alertcondition(currentAlerts.bearishFairValueGap,       'Bearish FVG',                  'Bearish FVG formed')

        # Liquidity Sweep Alerts
        ta.alertcondition(currentAlerts.bullishSweep, 'Bullish Sweep', 'Bullish liquidity sweep detected')
        ta.alertcondition(currentAlerts.bearishSweep, 'Bearish Sweep', 'Bearish liquidity sweep detected')

        # EMA Trend Alerts
        ema_trend_up = showEmaInput and emaTrend.bias == BULLISH and (pine.get_series_value([emaTrend.bias], 1) != BULLISH)
        ema_trend_down = showEmaInput and emaTrend.bias == BEARISH and (pine.get_series_value([emaTrend.bias], 1) != BEARISH)
        ta.alertcondition(ema_trend_up, 'EMA Trend Up', 'EMA trend turned bullish')
        ta.alertcondition(ema_trend_down, 'EMA Trend Down', 'EMA trend turned bearish')

        # Higher Timeframe EMA Trend Alerts
        ema_htf_trend_up = showEmaHtfInput and emaHtfTrend.bias == BULLISH and (pine.get_series_value([emaHtfTrend.bias], 1) != BULLISH)
        ema_htf_trend_down = showEmaHtfInput and emaHtfTrend.bias == BEARISH and (pine.get_series_value([emaHtfTrend.bias], 1) != BEARISH)
        ta.alertcondition(ema_htf_trend_up, 'Higher TF EMA Trend Up', 'Higher TF EMA trend turned bullish')
        ta.alertcondition(ema_htf_trend_down, 'Higher TF EMA Trend Down', 'Higher TF EMA trend turned bearish')

        # Signal Alerts
        ta.alertcondition(currentAlerts.buySignal, 'Buy Signal', 'Buy signal generated: EMA Trend Up (LTF) and EMA Trend Up (HTF)')
        ta.alertcondition(currentAlerts.sellSignal, 'Sell Signal', 'Sell signal generated: EMA Trend Down (LTF) and EMA Trend Down (HTF)')

# Example usage:
if __name__ == "__main__":
    # This is a conceptual example. In a real scenario, you would load actual OHLCV data.
    # Example data format: [{'open': 100, 'high': 105, 'low': 98, 'close': 103, 'time': 1678886400000, 'time_close': 1678972799999}]
    sample_data = [
        {'open': 100, 'high': 105, 'low': 98, 'close': 103, 'time': 1678886400000, 'time_close': 1678972799999},
        {'open': 103, 'high': 107, 'low': 101, 'close': 106, 'time': 1678972800000, 'time_close': 1679059199999},
        {'open': 106, 'high': 110, 'low': 104, 'close': 108, 'time': 1679059200000, 'time_close': 1679145599999},
        {'open': 108, 'high': 109, 'low': 102, 'close': 105, 'time': 1679145600000, 'time_close': 1679231999999},
        {'open': 105, 'high': 108, 'low': 100, 'close': 102, 'time': 1679232000000, 'time_close': 1679318399999},
        {'open': 102, 'high': 106, 'low': 99, 'close': 104, 'time': 1679318400000, 'time_close': 1679404799999},
        {'open': 104, 'high': 109, 'low': 103, 'close': 108, 'time': 1679404800000, 'time_close': 1679491199999},
        {'open': 108, 'high': 112, 'low': 107, 'close': 111, 'time': 1679491200000, 'time_close': 1679577599999},
        {'open': 111, 'high': 115, 'low': 110, 'close': 114, 'time': 1679577600000, 'time_close': 1679663999999},
        {'open': 114, 'high': 113, 'low': 109, 'close': 110, 'time': 1679664000000, 'time_close': 1679750399999},
    ]
    print("Running main strategy loop with sample data...")
    main_strategy_loop(sample_data)
    print("Strategy loop finished.")
