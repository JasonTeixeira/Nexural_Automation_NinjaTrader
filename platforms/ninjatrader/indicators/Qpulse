#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Data;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
	public class NexQPulsePro : Indicator
	{
		private Series<double> gainSeries;
		private Series<double> lossSeries;
		private Series<double> vwGainSeries;
		private Series<double> vwLossSeries;
		private Series<double> atrGainSeries;
		private Series<double> atrLossSeries;
		private Series<double> finalRsiSeries;
		private Series<double> volumeBaselineSeries;
		private Series<double> deltaSeries;
		private Series<double> cvdSeries;
		private Series<double> rvolSeries;
		private Series<double> vovSeries;
		private Series<double> dynObSeries;
		private Series<double> dynOsSeries;

		private ATR atr14;
		private SMA atr14Avg50;
		private SMA smaVol20;
		private SMA smaVol100;
		private MIN atrMin100;
		private MAX atrMax100;
		private StdDev atrStd20;

		[NinjaScriptProperty]
		[Display(Name = "Enable Hybrid", Order = 1, GroupName = "Core")]
		public bool EnableHybrid { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Volume Normalization", Order = 2, GroupName = "Core")]
		public bool EnableVolumeNormalization { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Advanced ATR", Order = 3, GroupName = "Core")]
		public bool EnableAdvancedAtr { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Volume Delta", Order = 4, GroupName = "Core")]
		public bool EnableVolumeDelta { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable RVOL", Order = 5, GroupName = "Core")]
		public bool EnableRvol { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable CVD Proxy", Order = 6, GroupName = "Core")]
		public bool EnableCvdProxy { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Direct VoV", Order = 7, GroupName = "Core")]
		public bool EnableDirectVoV { get; set; }

		[NinjaScriptProperty]
		[Range(1, 100)]
		[Display(Name = "RSI Length", Order = 8, GroupName = "Core")]
		public int Length { get; set; }

		[NinjaScriptProperty]
		[Range(50, 90)]
		[Display(Name = "Overbought", Order = 9, GroupName = "Core")]
		public double Overbought { get; set; }

		[NinjaScriptProperty]
		[Range(10, 50)]
		[Display(Name = "Oversold", Order = 10, GroupName = "Core")]
		public double Oversold { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 3.0)]
		[Display(Name = "VW Sensitivity", Order = 11, GroupName = "Core")]
		public double VwSensitivity { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 3.0)]
		[Display(Name = "ATR Sensitivity", Order = 12, GroupName = "Core")]
		public double AtrSensitivity { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 0.5)]
		[Display(Name = "Volume Norm Power", Order = 13, GroupName = "Core")]
		public double VolumeNormPower { get; set; }

		[NinjaScriptProperty]
		[Range(0.5, 2.0)]
		[Display(Name = "Advanced Sensitivity", Order = 14, GroupName = "Core")]
		public double AdvancedSensitivity { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Show Dynamic Zones", Order = 1, GroupName = "Visual")]
		public bool ShowZones { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Show Zero Line", Order = 2, GroupName = "Visual")]
		public bool ShowZeroLine { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Show Signal Arrows", Order = 3, GroupName = "Visual")]
		public bool ShowSignals { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Alerts", Order = 4, GroupName = "Visual")]
		public bool EnableAlerts { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Show Diagnostic Plots", Order = 5, GroupName = "Visual")]
		public bool ShowDiagnostics { get; set; }

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Name = "NexQPulsePro";
				Description = "QPulse Pro futures-ready NinjaTrader oscillator without dashboard/table.";
				IsOverlay = false;
				DrawOnPricePanel = false;
				IsSuspendedWhileInactive = true;

				EnableHybrid = true;
				EnableVolumeNormalization = true;
				EnableAdvancedAtr = true;
				EnableVolumeDelta = true;
				EnableRvol = true;
				EnableCvdProxy = true;
				EnableDirectVoV = true;

				Length = 6;
				Overbought = 70;
				Oversold = 30;
				VwSensitivity = 1.0;
				AtrSensitivity = 1.0;
				VolumeNormPower = 0.3;
				AdvancedSensitivity = 1.0;

				ShowZones = true;
				ShowZeroLine = true;
				ShowSignals = true;
				EnableAlerts = true;
				ShowDiagnostics = false;

				AddPlot(Brushes.LimeGreen, "QPulse");
				AddPlot(Brushes.White, "ZeroLine");
				AddPlot(Brushes.Red, "DynamicOB");
				AddPlot(Brushes.Lime, "DynamicOS");
				AddPlot(Brushes.DarkOrange, "VolumeDelta");
				AddPlot(Brushes.DeepSkyBlue, "RVOL");
				AddPlot(Brushes.MediumPurple, "CVDMomentum");
				AddPlot(Brushes.Gold, "VoVZScore");
			}
			else if (State == State.DataLoaded)
			{
				gainSeries = new Series<double>(this);
				lossSeries = new Series<double>(this);
				vwGainSeries = new Series<double>(this);
				vwLossSeries = new Series<double>(this);
				atrGainSeries = new Series<double>(this);
				atrLossSeries = new Series<double>(this);
				finalRsiSeries = new Series<double>(this);
				volumeBaselineSeries = new Series<double>(this);
				deltaSeries = new Series<double>(this);
				cvdSeries = new Series<double>(this);
				rvolSeries = new Series<double>(this);
				vovSeries = new Series<double>(this);
				dynObSeries = new Series<double>(this);
				dynOsSeries = new Series<double>(this);

				atr14 = ATR(14);
				atr14Avg50 = SMA(atr14, 50);
				smaVol20 = SMA(Volume, 20);
				smaVol100 = SMA(Volume, 100);
				atrMin100 = MIN(atr14, 100);
				atrMax100 = MAX(atr14, 100);
				atrStd20 = StdDev(atr14, 20);

				Plots[0].PlotStyle = PlotStyle.Bar;
				Plots[0].Width = 3;

				Plots[1].PlotStyle = PlotStyle.Line;
				Plots[1].Width = 2;

				Plots[2].PlotStyle = PlotStyle.Line;
				Plots[2].Width = 2;

				Plots[3].PlotStyle = PlotStyle.Line;
				Plots[3].Width = 2;

				Plots[4].PlotStyle = PlotStyle.Line;
				Plots[4].Width = 1;

				Plots[5].PlotStyle = PlotStyle.Line;
				Plots[5].Width = 1;

				Plots[6].PlotStyle = PlotStyle.Line;
				Plots[6].Width = 1;

				Plots[7].PlotStyle = PlotStyle.Line;
				Plots[7].Width = 1;
			}
		}

		protected override void OnBarUpdate()
		{
			if (CurrentBar == 0)
			{
				gainSeries[0] = 0;
				lossSeries[0] = 0;
				vwGainSeries[0] = 0;
				vwLossSeries[0] = 0;
				atrGainSeries[0] = 0;
				atrLossSeries[0] = 0;
				finalRsiSeries[0] = 0;
				volumeBaselineSeries[0] = Volume[0];
				deltaSeries[0] = 0;
				cvdSeries[0] = 0;
				rvolSeries[0] = 1;
				vovSeries[0] = 0;
				dynObSeries[0] = 80;
				dynOsSeries[0] = -80;

				Values[0][0] = 0;
				Values[1][0] = 0;
				Values[2][0] = 80;
				Values[3][0] = -80;
				Values[4][0] = double.NaN;
				Values[5][0] = double.NaN;
				Values[6][0] = double.NaN;
				Values[7][0] = double.NaN;
				return;
			}

			double src = Close[0];
			double change = src - Close[1];
			double gain = Math.Max(change, 0);
			double loss = Math.Abs(Math.Min(change, 0));

			gainSeries[0] = gain;
			lossSeries[0] = loss;

			double vol20 = Math.Max(smaVol20[0], 1);
			double vol100 = Math.Max(smaVol100[0], 1);
			double volumeFactor = Volume[0] / vol20;
			double adjustedVolumeFactor = Math.Pow(Math.Max(0.1, volumeFactor), VwSensitivity);

			double vwGain = gain * adjustedVolumeFactor;
			double vwLoss = loss * adjustedVolumeFactor;

			double smoothedVwGain = RecursiveEma(vwGain, vwGainSeries, Length);
			double smoothedVwLoss = RecursiveEma(vwLoss, vwLossSeries, Length);

			double safeVwGain = Math.Max(smoothedVwGain, 0.0001);
			double safeVwLoss = Math.Max(smoothedVwLoss, 0.0001);
			double vwRs = safeVwGain / safeVwLoss;
			double vwRsi = 100.0 - (100.0 / (1.0 + vwRs));
			double centeredVwRsi = Clamp((vwRsi - 50.0) * 4.0, -200.0, 200.0);

			double currentAtr = EnableAdvancedAtr ? atr14[0] * AdvancedSensitivity : atr14[0];
			double avgAtr = Math.Max(atr14Avg50[0], 0.0001);
			double atrRatio = currentAtr / avgAtr;
			double adjustedAtrRatio = Math.Pow(Math.Max(0.1, Math.Min(5.0, atrRatio)), AtrSensitivity);

			double lengthMultiplier = 2.0 - Math.Min(1.8, adjustedAtrRatio);
			int adaptiveLength = Math.Max(2, Math.Min(50, (int)Math.Round(Length * lengthMultiplier)));

			double atrGain = RecursiveEma(gain, atrGainSeries, adaptiveLength);
			double atrLoss = RecursiveEma(loss, atrLossSeries, adaptiveLength);

			double safeAtrGain = Math.Max(atrGain, 0.0001);
			double safeAtrLoss = Math.Max(atrLoss, 0.0001);
			double atrRs = safeAtrGain / safeAtrLoss;
			double atrRsi = 100.0 - (100.0 / (1.0 + atrRs));
			double centeredAtrRsi = Clamp((atrRsi - 50.0) * 4.0, -200.0, 200.0);

			double rawFinalRsi = EnableHybrid
				? centeredVwRsi * 0.5 + centeredAtrRsi * 0.5
				: centeredAtrRsi;

			double volumeBaseline = vol100;
			volumeBaselineSeries[0] = volumeBaseline;

			double volumeParticipation = 1.0;
			if (EnableVolumeNormalization)
			{
				double volRatio = Volume[0] / Math.Max(volumeBaseline, 1);
				double volRatioCapped = Math.Min(volRatio, 2.0);
				volumeParticipation = Math.Pow(Math.Max(0.1, volRatioCapped), VolumeNormPower);
			}

			double volumeAdjustedRsi = rawFinalRsi * volumeParticipation;
			double signalThreshold = 60.0;
			double dampeningFactor = Math.Abs(volumeAdjustedRsi) < signalThreshold ? 0.3 : 1.0;
			double finalRsi = volumeAdjustedRsi * dampeningFactor;
			finalRsiSeries[0] = finalRsi;

			double hlRange = High[0] - Low[0];
			double safeRange = Math.Max(hlRange, TickSize);
			double closePosition = (Close[0] - Low[0]) / safeRange;
			double delta = EnableVolumeDelta ? Volume[0] * (2.0 * closePosition - 1.0) : 0.0;
			deltaSeries[0] = delta;

			if (Bars.IsFirstBarOfSession)
				cvdSeries[0] = delta;
			else
				cvdSeries[0] = cvdSeries[1] + delta;

			double cvdFast = EMA(cvdSeries, 20)[0];
			double cvdSlow = EMA(cvdSeries, 50)[0];
			double cvdMomentum = EnableCvdProxy ? (cvdFast - cvdSlow) / Math.Max(Math.Abs(cvdSlow), 0.0001) : 0.0;

			double rvol = EnableRvol ? Volume[0] / vol20 : 1.0;
			rvolSeries[0] = rvol;

			double atrMean20 = Math.Max(SMA(atr14, 20)[0], 0.0001);
			double vov = EnableDirectVoV ? atrStd20[0] / atrMean20 : 0.0;
			vovSeries[0] = vov;

			double vovMean = CurrentBar >= 50 ? SMA(vovSeries, 50)[0] : 0.0;
			double vovStd = CurrentBar >= 50 ? Math.Max(StdDev(vovSeries, 50)[0], 0.0001) : 1.0;
			double vovZ = EnableDirectVoV ? (vov - vovMean) / vovStd : 0.0;

			double baseOb = ((Overbought - 50.0) * 2.0) * 2.0;
			double baseOs = ((Oversold - 50.0) * 2.0) * 2.0;

			double atrLookbackLow = atrMin100[0];
			double atrLookbackHigh = atrMax100[0];
			double atrRange100 = Math.Max(atrLookbackHigh - atrLookbackLow, 0.0001);
			double atrPercent = ((atr14[0] - atrLookbackLow) / atrRange100) * 100.0;

			double volAdjustment = (atrPercent - 50.0) * 1.0;
			double dynamicOb = Clamp(baseOb + volAdjustment, -170.0, 170.0);
			double dynamicOs = Clamp(baseOs - volAdjustment, -170.0, 170.0);

			dynObSeries[0] = dynamicOb;
			dynOsSeries[0] = dynamicOs;

			Values[0][0] = finalRsi;
			Values[1][0] = ShowZeroLine ? 0 : double.NaN;
			Values[2][0] = ShowZones ? dynamicOb : double.NaN;
			Values[3][0] = ShowZones ? dynamicOs : double.NaN;
			Values[4][0] = ShowDiagnostics ? delta : double.NaN;
			Values[5][0] = ShowDiagnostics ? rvol : double.NaN;
			Values[6][0] = ShowDiagnostics ? cvdMomentum * 100.0 : double.NaN;
			Values[7][0] = ShowDiagnostics ? vovZ * 20.0 : double.NaN;

			PlotBrushes[0][0] = finalRsi >= 0 ? Brushes.LimeGreen : Brushes.Red;
			PlotBrushes[1][0] = Brushes.White;
			PlotBrushes[2][0] = Brushes.Red;
			PlotBrushes[3][0] = Brushes.Lime;
			PlotBrushes[4][0] = Brushes.DarkOrange;
			PlotBrushes[5][0] = Brushes.DeepSkyBlue;
			PlotBrushes[6][0] = Brushes.MediumPurple;
			PlotBrushes[7][0] = Brushes.Gold;

			bool bullishSignal =
				CrossAbove(finalRsiSeries, dynOsSeries, 1) &&
				finalRsi > 0 &&
				delta >= 0 &&
				cvdMomentum >= -0.05;

			bool bearishSignal =
				CrossBelow(finalRsiSeries, dynObSeries, 1) &&
				finalRsi < 0 &&
				delta <= 0 &&
				cvdMomentum <= 0.05;

			if (ShowSignals)
			{
				if (bullishSignal)
					Draw.ArrowUp(this, "QPulseBull" + CurrentBar, false, 0, finalRsi - 12, Brushes.LimeGreen);

				if (bearishSignal)
					Draw.ArrowDown(this, "QPulseBear" + CurrentBar, false, 0, finalRsi + 12, Brushes.Red);
			}

			if (EnableAlerts)
			{
				if (bullishSignal)
					Alert("QPulseBull" + CurrentBar, Priority.Medium, "QPulse bullish signal", NinjaTrader.Core.Globals.InstallDir + @"\sounds\Alert3.wav", 10, Brushes.LimeGreen, Brushes.Black);

				if (bearishSignal)
					Alert("QPulseBear" + CurrentBar, Priority.Medium, "QPulse bearish signal", NinjaTrader.Core.Globals.InstallDir + @"\sounds\Alert3.wav", 10, Brushes.Red, Brushes.Black);
			}
		}

		private double RecursiveEma(double inputValue, Series<double> storageSeries, int len)
		{
			double alpha = 2.0 / (len + 1.0);
			double prev = CurrentBar > 0 ? storageSeries[1] : inputValue;
			double result = alpha * inputValue + (1.0 - alpha) * prev;
			storageSeries[0] = result;
			return result;
		}

		private double Clamp(double value, double min, double max)
		{
			return Math.Min(Math.Max(value, min), max);
		}

		[Browsable(false)]
		[XmlIgnore]
		public Series<double> QPulse
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
		private NexQPulsePro[] cacheNexQPulsePro;
		public NexQPulsePro NexQPulsePro(bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			return NexQPulsePro(Input, enableHybrid, enableVolumeNormalization, enableAdvancedAtr, enableVolumeDelta, enableRvol, enableCvdProxy, enableDirectVoV, length, overbought, oversold, vwSensitivity, atrSensitivity, volumeNormPower, advancedSensitivity, showZones, showZeroLine, showSignals, enableAlerts, showDiagnostics);
		}

		public NexQPulsePro NexQPulsePro(ISeries<double> input, bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			if (cacheNexQPulsePro != null)
				for (int idx = 0; idx < cacheNexQPulsePro.Length; idx++)
					if (cacheNexQPulsePro[idx] != null && cacheNexQPulsePro[idx].EnableHybrid == enableHybrid && cacheNexQPulsePro[idx].EnableVolumeNormalization == enableVolumeNormalization && cacheNexQPulsePro[idx].EnableAdvancedAtr == enableAdvancedAtr && cacheNexQPulsePro[idx].EnableVolumeDelta == enableVolumeDelta && cacheNexQPulsePro[idx].EnableRvol == enableRvol && cacheNexQPulsePro[idx].EnableCvdProxy == enableCvdProxy && cacheNexQPulsePro[idx].EnableDirectVoV == enableDirectVoV && cacheNexQPulsePro[idx].Length == length && cacheNexQPulsePro[idx].Overbought == overbought && cacheNexQPulsePro[idx].Oversold == oversold && cacheNexQPulsePro[idx].VwSensitivity == vwSensitivity && cacheNexQPulsePro[idx].AtrSensitivity == atrSensitivity && cacheNexQPulsePro[idx].VolumeNormPower == volumeNormPower && cacheNexQPulsePro[idx].AdvancedSensitivity == advancedSensitivity && cacheNexQPulsePro[idx].ShowZones == showZones && cacheNexQPulsePro[idx].ShowZeroLine == showZeroLine && cacheNexQPulsePro[idx].ShowSignals == showSignals && cacheNexQPulsePro[idx].EnableAlerts == enableAlerts && cacheNexQPulsePro[idx].ShowDiagnostics == showDiagnostics && cacheNexQPulsePro[idx].EqualsInput(input))
						return cacheNexQPulsePro[idx];
			return CacheIndicator<NexQPulsePro>(new NexQPulsePro(){ EnableHybrid = enableHybrid, EnableVolumeNormalization = enableVolumeNormalization, EnableAdvancedAtr = enableAdvancedAtr, EnableVolumeDelta = enableVolumeDelta, EnableRvol = enableRvol, EnableCvdProxy = enableCvdProxy, EnableDirectVoV = enableDirectVoV, Length = length, Overbought = overbought, Oversold = oversold, VwSensitivity = vwSensitivity, AtrSensitivity = atrSensitivity, VolumeNormPower = volumeNormPower, AdvancedSensitivity = advancedSensitivity, ShowZones = showZones, ShowZeroLine = showZeroLine, ShowSignals = showSignals, EnableAlerts = enableAlerts, ShowDiagnostics = showDiagnostics }, input, ref cacheNexQPulsePro);
		}
	}
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
	public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
	{
		public Indicators.NexQPulsePro NexQPulsePro(bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			return indicator.NexQPulsePro(Input, enableHybrid, enableVolumeNormalization, enableAdvancedAtr, enableVolumeDelta, enableRvol, enableCvdProxy, enableDirectVoV, length, overbought, oversold, vwSensitivity, atrSensitivity, volumeNormPower, advancedSensitivity, showZones, showZeroLine, showSignals, enableAlerts, showDiagnostics);
		}

		public Indicators.NexQPulsePro NexQPulsePro(ISeries<double> input , bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			return indicator.NexQPulsePro(input, enableHybrid, enableVolumeNormalization, enableAdvancedAtr, enableVolumeDelta, enableRvol, enableCvdProxy, enableDirectVoV, length, overbought, oversold, vwSensitivity, atrSensitivity, volumeNormPower, advancedSensitivity, showZones, showZeroLine, showSignals, enableAlerts, showDiagnostics);
		}
	}
}

namespace NinjaTrader.NinjaScript.Strategies
{
	public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
	{
		public Indicators.NexQPulsePro NexQPulsePro(bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			return indicator.NexQPulsePro(Input, enableHybrid, enableVolumeNormalization, enableAdvancedAtr, enableVolumeDelta, enableRvol, enableCvdProxy, enableDirectVoV, length, overbought, oversold, vwSensitivity, atrSensitivity, volumeNormPower, advancedSensitivity, showZones, showZeroLine, showSignals, enableAlerts, showDiagnostics);
		}

		public Indicators.NexQPulsePro NexQPulsePro(ISeries<double> input , bool enableHybrid, bool enableVolumeNormalization, bool enableAdvancedAtr, bool enableVolumeDelta, bool enableRvol, bool enableCvdProxy, bool enableDirectVoV, int length, double overbought, double oversold, double vwSensitivity, double atrSensitivity, double volumeNormPower, double advancedSensitivity, bool showZones, bool showZeroLine, bool showSignals, bool enableAlerts, bool showDiagnostics)
		{
			return indicator.NexQPulsePro(input, enableHybrid, enableVolumeNormalization, enableAdvancedAtr, enableVolumeDelta, enableRvol, enableCvdProxy, enableDirectVoV, length, overbought, oversold, vwSensitivity, atrSensitivity, volumeNormPower, advancedSensitivity, showZones, showZeroLine, showSignals, enableAlerts, showDiagnostics);
		}
	}
}

#endregion
