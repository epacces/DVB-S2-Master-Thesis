set terminal lua fulldoc monochrome \
plotsize 9,6.5
set output 'bound.tex'
unset key
set format x '$10^{%T}$'
set xrange [ 1e-2 : 40]
set yrange [-5 : 100]
set logscale x
set label '\small \sl Power limited' at 0.04, 70
set label '\small \sl Bandwidth limited' at 1.2, 85
set label '$\mathsmall -1.6 \mathrm{dB}$' at 9, 1.5
set xlabel 'Sprectral efficiency $\eta= R\ped_b/W$'
set ylabel 'Signal-to-Noise-Ratio $E\ped b / N\ped 0$'
f(x) = 10*log10((2**x-1)/x)
set samples 150, 150
delta(x) = x<=1 ? -5:100
plot f(x)  lc -1 lw 2,  -1.4 lc -2, delta(x) lc -2 with histeps



