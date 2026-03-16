#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Data;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
	public class NexJMA : Indicator
	{
		private Series<double> e0Series;
		private Series<double> e1Series;
		private Series<double> e2Series;
		private Series<double> jmaSeries;

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name = "Length", Order = 1, GroupName = "Parameters")]
		public int Length { get; set; }

		[NinjaScriptProperty]
		[Range(-100, 100)]
		[Display(Name = "Phase", Order = 2, GroupName = "Parameters")]
		public int Phase { get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name = "Power", Order = 3, GroupName = "Parameters")]
		public int Power { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Highlight Movements", Order = 4, GroupName = "Parameters")]
		public bool HighlightMovements { get; set; }

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Name = "NexJMA";
				Description = "Strict Pine-to-NinjaTrader Jurik Moving Average translation.";
				IsOverlay = true;
				IsSuspendedWhileInactive = true;

				Length = 7;
				Phase = 50;
				Power = 2;
				HighlightMovements = true;

				AddPlot(Brushes.Green, "JMA");
			}
			else if (State == State.DataLoaded)
			{
				e0Series = new Series<double>(this);
				e1Series = new Series<double>(this);
				e2Series = new Series<double>(this);
				jmaSeries = new Series<double>(this);
			}
		}

		protected override void OnBarUpdate()
		{
			double phaseRatio = Phase < -100 ? 0.5 : Phase > 100 ? 2.5 : Phase / 100.0 + 1.5;
			double beta = 0.45 * (Length - 1.0) / (0.45 * (Length - 1.0) + 2.0);
			double alpha = Math.Pow(beta, Power);

			double prevE0 = CurrentBar > 0 ? e0Series[1] : 0.0;
			double prevE1 = CurrentBar > 0 ? e1Series[1] : 0.0;
			double prevE2 = CurrentBar > 0 ? e2Series[1] : 0.0;
			double prevJma = CurrentBar > 0 ? jmaSeries[1] : 0.0;

			double src = Input[0];

			double e0 = (1.0 - alpha) * src + alpha * prevE0;
			double e1 = (src - e0) * (1.0 - beta) + beta * prevE1;
			double e2 = (e0 + phaseRatio * e1 - prevJma) * Math.Pow(1.0 - alpha, 2.0) + Math.Pow(alpha, 2.0) * prevE2;
			double jma = e2 + prevJma;

			e0Series[0] = e0;
			e1Series[0] = e1;
			e2Series[0] = e2;
			jmaSeries[0] = jma;

			Value[0] = jma;

			if (HighlightMovements)
				PlotBrushes[0][0] = CurrentBar > 0 && jma > jmaSeries[1] ? Brushes.Green : Brushes.Red;
			else
				PlotBrushes[0][0] = Brushes.MediumPurple;
		}

		[Browsable(false)]
		[XmlIgnore]
		public Series<double> JMA
		{
			get { return Values[0]; }
		}
	}
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
	public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
	{
		private NexJMA[] cacheNexJMA;
		public NexJMA NexJMA(int length, int phase, int power, bool highlightMovements)
		{
			return NexJMA(Input, length, phase, power, highlightMovements);
		}

		public NexJMA NexJMA(ISeries<double> input, int length, int phase, int power, bool highlightMovements)
		{
			if (cacheNexJMA != null)
				for (int idx = 0; idx < cacheNexJMA.Length; idx++)
					if (cacheNexJMA[idx] != null && cacheNexJMA[idx].Length == length && cacheNexJMA[idx].Phase == phase && cacheNexJMA[idx].Power == power && cacheNexJMA[idx].HighlightMovements == highlightMovements && cacheNexJMA[idx].EqualsInput(input))
						return cacheNexJMA[idx];
			return CacheIndicator<NexJMA>(new NexJMA(){ Length = length, Phase = phase, Power = power, HighlightMovements = highlightMovements }, input, ref cacheNexJMA);
		}
	}
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
	public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
	{
		public Indicators.NexJMA NexJMA(int length, int phase, int power, bool highlightMovements)
		{
			return indicator.NexJMA(Input, length, phase, power, highlightMovements);
		}

		public Indicators.NexJMA NexJMA(ISeries<double> input , int length, int phase, int power, bool highlightMovements)
		{
			return indicator.NexJMA(input, length, phase, power, highlightMovements);
		}
	}
}

namespace NinjaTrader.NinjaScript.Strategies
{
	public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
	{
		public Indicators.NexJMA NexJMA(int length, int phase, int power, bool highlightMovements)
		{
			return indicator.NexJMA(Input, length, phase, power, highlightMovements);
		}

		public Indicators.NexJMA NexJMA(ISeries<double> input , int length, int phase, int power, bool highlightMovements)
		{
			return indicator.NexJMA(input, length, phase, power, highlightMovements);
		}
	}
}

#endregion
