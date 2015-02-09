--[[

  This is the execution script of the `Lua generic terminal' driver.
  
  This script provides an interface to the PGF/TikZ package for
  TeX, LaTeX and ConTeXt...

  
  Copyright (C) 2007    Peter Hedwig <peter@affenbande.org>

  
  
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


  $Date: 2007-09-30 01:18:06 +0200 (So, 30 Sep 2007) $
  $Author: peter $
  $Rev: 69 $


]]--



--[[
 
 `term'   gnuplot -> local interface
 `gp'     local -> gnuplot interface

  are both initialized by the terminal

]]--


-- when called from the command line we have
-- to initialize the table `term' manually
-- to avoid errors
if arg then
  term = {}
else
  --
  -- gnuplot terminal parameters and flags
  --
  -- 10000 => 4 digit resolution
  term.xmax = 10000
  term.ymax = 10000
  term.h_tic =  100
  term.v_tic =  100
  -- depends on the used font
  -- and xmax/ymax !!!
  term.h_char = 160
  term.v_char = 360
  term.description = "Lua PGF/TikZ terminal for LaTeX2e"
  term.flags = term.TERM_BINARY + term.TERM_CAN_CLIP
                + term.TERM_IS_POSTSCRIPT + term.TERM_CAN_MULTIPLOT
end


--
-- internal variables
--

local pgf = {}
local gfx = {}


pgf.LATEX_STYLE_FILE = "gnuplot-lua-tikz"  -- \usepackage{gnuplot-lua-tikz}

pgf.REVISION = string.sub("$Rev: 69 $",7,-3)
pgf.REVISION_DATE = string.gsub("$Date: 2007-09-30 01:18:06 +0200 (So, 30 Sep 2007) $",
                                "$Date: ([0-9]+)-([0-9]+)-([0-9]+) .*","%1/%2/%3")

pgf.styles = {}

-- plot styles are coresponding with linetypes and must have the same number of entries
-- see option 'tikzplot' for usage
pgf.styles.plotstyles = {
   [1] = {"gp plot solid", ""},
   [2] = {"gp plot border", ""},
   [3] = {"gp plot axes", ""},
   [4] = {"gp plot 0", "smooth"},
   [5] = {"gp plot 1", "smooth"},
   [6] = {"gp plot 2", "smooth"},
   [7] = {"gp plot 3", "smooth"},
   [8] = {"gp plot 4", "smooth"},
   [9] = {"gp plot 5", "smooth"},
   [10] = {"gp plot 6", "smooth"},
   [11] = {"gp plot 7", "smooth"}
}

pgf.styles.linetypes = {
   [1] = {"gp_lt_solid", "solid"},  -- An lt of -3 is solid and drawn with xor (for temporary interactive annotations).
   [2] = {"gp_lt_border", "solid"}, -- An lt of -2 is used for the border of the plot.
   [3] = {"gp_lt_axes", "dashed"},  -- An lt of -1 is used for the X and Y axes.  
   [4] = {"gp_lt_plot0", "solid"},  -- first graph
   [5] = {"gp_lt_plot1", "dashed"}, -- second ...
   [6] = {"gp_lt_plot2", "dash pattern=on 1.5pt off 2.25pt"},
   [7] = {"gp_lt_plot3", "dash pattern=on \\pgflinewidth off 1.125"},
   [8] = {"gp_lt_plot4", "dash pattern=on 4.5pt off 1.5pt on \\pgflinewidth off 1.5pt"},
   [9] = {"gp_lt_plot5", "dash pattern=on 2.25pt off 2.25pt on \\pgflinewidth off 2.25pt"},
  [10] = {"gp_lt_plot6", "dash pattern=on 1.5pt off 1.5pt on 1.5pt off 4.5pt"},
  [11] = {"gp_lt_plot7", "dash pattern=on \\pgflinewidth off 1.5pt on 4.5pt off 1.5pt on \\pgflinewidth off 1.5pt"}
}

-- corresponds to pgf.styles.linetypes
pgf.styles.lt_colors = {
  [1] = {"gp_lt_color_s", "black"},
  [2] = {"gp_lt_color_b", "black"},
  [3] = {"gp_lt_color_a", "black"},
  [4] = {"gp_lt_color0", "red"},
  [5] = {"gp_lt_color1", "green!60!black"},
  [6] = {"gp_lt_color2", "blue"},
  [7] = {"gp_lt_color3", "magenta"},
  [8] = {"gp_lt_color4", "cyan"},
  [9] = {"gp_lt_color5", "orange"},
 [10] = {"gp_lt_color6", "yellow!80!red"},
 [11] = {"gp_lt_color7", "blue!80!black"}
}

pgf.styles.patterns = {
  [1] = {"gp_pattern0", "white"},
  [2] = {"gp_pattern1", "pattern=north east lines"},
  [3] = {"gp_pattern2", "pattern=north west lines"},
  [4] = {"gp_pattern3", "pattern=crosshatch"},
  [5] = {"gp_pattern4", "pattern=grid"},
  [6] = {"gp_pattern5", "pattern=vertical lines"},
  [7] = {"gp_pattern6", "pattern=horizontal lines"},
  [8] = {"gp_pattern7", "pattern=dots"},
  [9] = {"gp_pattern8", "pattern=crosshatch dots"},
 [10] = {"gp_pattern9", "pattern=fivepointed stars"},
 [11] = {"gp_pattern10", "pattern=sixpointed stars"},
 [12] = {"gp_pattern11", "pattern=bricks"}
}


pgf.styles.plotmarks = {
  [1] = {"gp_mark0", "mark size=.5\\pgflinewidth,mark=*"}, -- point (-1)
  [2] = {"gp_mark1", "mark=+"},
  [3] = {"gp_mark2", "mark=x"},
  [4] = {"gp_mark3", "mark=star"},
  [5] = {"gp_mark4", "mark=square"},
  [6] = {"gp_mark5", "mark=square*"},
  [7] = {"gp_mark6", "mark=o"},
  [8] = {"gp_mark7", "mark=*"},
  [9] = {"gp_mark8", "mark=triangle"},
 [10] = {"gp_mark9", "mark=triangle*"},
 [11] = {"gp_mark10", "mark=triangle,mark options={rotate=180}"},
 [12] = {"gp_mark11", "mark=triangle*,mark options={rotate=180}"},
 [13] = {"gp_mark12", "mark=diamond"},
 [14] = {"gp_mark13", "mark=diamond*"},
 [15] = {"gp_mark14", "mark=otimes"},
 [16] = {"gp_mark15", "mark=oplus"}
}  


--[[===============================================================================================

  The PGF/TikZ output routines

]]--===============================================================================================

pgf.transform_xcoord = function(coord)
  return (coord+gfx.origin_xoffset)*gfx.scalex
end

pgf.transform_ycoord = function(coord)
  return (coord+gfx.origin_yoffset)*gfx.scaley
end

pgf.format_coord = function(xc, yc)
  return string.format("%.3f,%.3f", pgf.transform_xcoord(xc), pgf.transform_ycoord(yc))
end

pgf.doc_begin = function(preamble)
  gp.write("\\documentclass[10pt,a4paper]{scrartcl}\n"
        .."\\usepackage[T1]{fontenc}\n"
        .."\\usepackage{textcomp}\n\n"
        .."\\usepackage[utf8x]{inputenc}\n\n"
        .."\\usepackage{"..pgf.LATEX_STYLE_FILE.."}\n"
        ..preamble.."\n\n"
        .."\\begin{document}\n")
end

pgf.doc_end = function()
  gp.write("\\end{document}\n")  
end

pgf.graph_begin = function (font, noenv)
  local global_opt = "" -- unused
  if noenv then
    gp.write("%% ") -- comment out
  end
  gp.write(string.format("\\begin{tikzpicture}[gnuplot%s]\n",global_opt))
  gp.write(string.format("%%%% generated with GNUPLOT %sp%s (%s; terminal rev. %s, script rev. %s)\n%%%% %s\n",
      term.gp_version, term.gp_patchlevel,
      string.match(term.lua_ident, "Lua [0-9\.]+"),
      string.sub(term.lua_term_revision,7,-3),
      pgf.REVISION,os.date()))
  if font ~= "" then
    gp.write(string.format("\\tikzstyle{every node}+=[font=%s]\n", font))
  end
  if not gfx.opt.lines_dashed then
    gp.write("\\gpsolidlines\n")
  end
  if not gfx.opt.lines_colored then
    gp.write("\\gpmonochromelines\n")
  end
end

pgf.graph_end = function(noenv)
  if noenv then
    gp.write("%% ") -- comment out
  end
  gp.write("\\end{tikzpicture}\n")
end

pgf.draw_path = function(t)

  local use_plot = false
  local c_str = '--'

  -- is the current linetype in the list of plots?
  if #gfx.opt.plot_list > 0 then
    for k, v in pairs(gfx.opt.plot_list) do
      if gfx.linetype_idx_set == v  then
        use_plot = true
        c_str = ' '
        break
      end
    end
  end

  gp.write("\\draw[gp path] ")
  if use_plot then
    gp.write("plot["..pgf.styles.plotstyles[((gfx.linetype_idx_set+3) % #pgf.styles.plotstyles)+1][1].."] coordinates {")
  end
  gp.write("("..pgf.format_coord(t[1][1], t[1][2])..")")
  for i = 2,#t-1 do
    -- pretty printing
    if (i % 5) == 0 then
      gp.write("%\n  ")
    end
    gp.write(c_str.."("..pgf.format_coord(t[i][1], t[i][2])..")")
  end
  -- check for a cyclic path
  if #t > 1 and t[1][1] == t[#t][1] and t[1][2] == t[#t][2] and not use_plot then
    gp.write("--cycle")
  else
    gp.write(c_str.."("..pgf.format_coord(t[#t][1], t[#t][2])..")")
  end
  if use_plot then
    gp.write("}")
  end
  gp.write(";\n")
end


pgf.draw_arrow = function(t, direction, headstyle)
  gp.write("\\draw[gp path,"..direction.."]")
  gp.write("("..pgf.format_coord(t[1][1], t[1][2])..")")
  for i = 2,#t do
    if (i % 5) == 0 then
      gp.write("%\n  ")
    end
    gp.write("--("..pgf.format_coord(t[i][1], t[i][2])..")")
  end
  gp.write(";\n")
end


pgf.draw_points = function(t, pm)
  gp.write("\\gppoint{"..pm.."}{")
  for i,v in ipairs(t) do
      gp.write("("..pgf.format_coord(v[1], v[2])..")")
  end
  gp.write("}\n")
end


pgf.set_linetype = function(linetype)
  gp.write("\\gpsetlinetype{"..linetype.."}\n")
end


pgf.set_color = function(color)
  gp.write("\\color{"..color.."}\n")
end


pgf.set_linewidth = function(width)
  gp.write(string.format("\\gpsetlinewidth{%.2f}\n", width))
end


pgf.set_pointsize = function(size)
  gp.write(string.format("\\gpsetpointsize{%.2f}\n", 4*size))
end


pgf.draw_text = function(t, text, angle, justification, font)
  local node_options = justification
  if angle ~= 0 then
    node_options = node_options .. ",rotate=" .. angle
  end
  if font ~= "" then
    node_options = node_options .. ",font=" .. font
  end  
  gp.write(string.format("\\node[%s] at (%s) {%s};\n", 
          node_options, pgf.format_coord(t[1], t[2]), text))
end


pgf.draw_fill = function(t, pattern, color, saturation, opacity)
  local fill_path = ''
  local fill_style = ''
  
  if saturation < 100 then
    gp.write("\\begin{colormixin}{"..saturation.."!white}\n")
  end

  fill_path = fill_path .. '('..pgf.format_coord(t[1][1], t[1][2])..')'
  -- draw 2nd to n-1 corners
  for i = 2,#t-1 do
    if (i % 5) == 0 then
      -- pretty printing
      fill_path = fill_path .. "%\n    "
    end
    fill_path = fill_path .. '--('..pgf.format_coord(t[i][1], t[i][2])..')'
  end
  -- draw last corner
  -- 'cycle' is just for the case that we want to draw a
  -- line around the filled area
  if t[1][1] == t[#t][1] and t[1][2] == t[#t][2] then -- cyclic
    fill_path = fill_path .. '--cycle'
  else
    fill_path = fill_path
          .. '--('..pgf.format_coord(t[#t][1], t[#t][2])..')--cycle'
  end
  
  if pattern == '' then
    -- solid fills
    fill_style = 'color='..color
    if opacity < 100 then
      fill_style = fill_style..string.format(",opacity=%.2f", opacity/100)
    else
      -- fill_style = "" -- color ?
    end
  else
    -- pattern fills
    fill_style = pattern..',pattern color='..color
  end
  local out = ''
  if pattern ~= '' and opacity == 100 then
    -- have to fill bg for opaque patterns
    gp.write("\\def\\gpfillpath{"..fill_path.."}\n"
          .. "\\gpfill{color=gpbgfillcolor} \\gpfillpath;\n"
          .. "\\gpfill{"..fill_style.."} \\gpfillpath;\n")
  else
    gp.write("\\gpfill{"..fill_style.."} "..fill_path..";\n")
  end
  
  if saturation < 100 then
    gp.write("\\end{colormixin}\n")
  end
end

pgf.raw_rgb_image = function(t, m, n, ll, ur)
  local gw = gp.write
  local sf = string.format
  local xs = sf("%.3f", pgf.transform_xcoord(ur[1]) - pgf.transform_xcoord(ll[1]))
  local ys = sf("%.3f", pgf.transform_ycoord(ur[2]) - pgf.transform_ycoord(ll[2]))
  gp.write("\\def\\gprawrgbimagedata{%\n  ")
  for cnt = 1,#t do
    gw(sf("%02x%02x%02x",255*t[cnt][1]+0.5,255*t[cnt][2]+0.5,255*t[cnt][3]+0.5))
    if cnt % 16 == 0 then
      gw("%\n  ")
    end
  end
  gp.write("}%\n")
  gp.write("\\gprawrgbimage{"..sf("%.3f", pgf.transform_xcoord(ll[1])).."}"
      .."{"..sf("%.3f", pgf.transform_ycoord(ll[2])).."}"
      .."{"..m.."}{"..n.."}{"..xs.."}{"..ys.."}{\\gprawrgbimagedata}\n")
end

pgf.start_clipbox = function (ll,ur)
  gp.write("\\begin{scope}\n")
  gp.write(string.format("\\clip (%s) rectangle (%s);\n",
      pgf.format_coord(ll[1],ll[2]),pgf.format_coord(ur[1],ur[2])))
end

pgf.end_clipbox = function()
  gp.write("\\end{scope}\n")
end

pgf.write_boundingbox = function(t, num)
  gp.write("%% coordinates of the plot area\n")
  gp.write("\\coordinate (gpbb south west "..num..") at ("..pgf.format_coord(t.xleft,t.ybot)..");\n")
  gp.write("\\coordinate (gpbb south east "..num..") at ("..pgf.format_coord(t.xright,t.ybot)..");\n")
  gp.write("\\coordinate (gpbb north east "..num..") at ("..pgf.format_coord(t.xright,t.ytop)..");\n")
  gp.write("\\coordinate (gpbb north west "..num..") at ("..pgf.format_coord(t.xleft,t.ytop)..");\n")
end

pgf.write_variables = function(t)
  gp.write("%% gnuplot variables\n")
  for k, v in pairs(t) do
    gp.write(string.format("\\gpsetvar{%s}{%s}\n",k,v))
  end
end

-- write style to seperate file, or whatever...
pgf.create_style = function(f)
f:write([[
%%
%%  This is the style file for the gnuplot PGF/TikZ terminal
%%  
%%  It is associated with the 'gnuplot.lua' script, and usually generated
%%  automatically. So take care whenever you make any changes!
%%
\NeedsTeXFormat{LaTeX2e}
]])
f:write("\\ProvidesPackage{"..pgf.LATEX_STYLE_FILE.."}%\n")
f:write("          ["..pgf.REVISION_DATE.." (rev. "..pgf.REVISION..") GNUPLOT Lua terminal style]\n\n")
f:write([[
\RequirePackage{tikz}
\RequirePackage{xxcolor}
\RequirePackage{ifpdf}
\RequirePackage{ifxetex}

\usetikzlibrary{arrows,patterns,plotmarks}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%  
%%

%
% image related stuff
%
\def\gp@rawrgbimage@pdf#1#2#3#4#5{%
    \pgf@sys@bp{#3}\pgfsysprotocol@literalbuffered{0 0}\pgf@sys@bp{#4}\pgfsysprotocol@literalbuffered{0 0 cm}%
    \pgfsysprotocol@literal{BI /W #1 /H #2 /CS /RGB /BPC 8 /F /AHx ID #5 > EI}%
}
\def\gp@rawrgbimage@ps#1#2#3#4#5{%
      \pgfsysprotocol@literalbuffered{0 0 translate}%
      \pgf@sys@bp{#3}\pgf@sys@bp{#4}\pgfsysprotocol@literalbuffered{scale}%
      \pgfsysprotocol@literalbuffered{#1 #2 8 [#1 0 0 -#2 0 #2]}%
      \pgfsysprotocol@literal{{<#5>} false 3 colorimage}%
}

\ifpdf
  \def\gp@rawrgbimage{\gp@rawrgbimage@pdf}
\else
  \ifxetex
    \def\gp@rawrgbimage{\gp@rawrgbimage@pdf}
  \else
    \def\gp@rawrgbimage{\gp@rawrgbimage@ps}
  \fi
\fi

\def\gp@set@size#1{%
  \def\gp@image@size{#1}%
}
%% \gprawrgbimage{xcoord}{ycoord}{# of xpixel}{# of ypixel}{xsize}{ysize}{rgb hex data RRGGBB}
\def\gprawrgbimage#1#2#3#4#5#6#7{%
  \tikz@scan@one@point\gp@set@size(#5,#6)\relax%
  \tikz@scan@one@point\pgftransformshift(#1,#2)\relax%
  \pgftext {%
    \pgfsys@beginpurepicture%
    \gp@image@size% fill \pgf@x and \pgf@y
    \gp@rawrgbimage{#3}{#4}{\pgf@x}{\pgf@y}{#7}%
    \pgfsys@endpurepicture%
  }%
}

%
% gnuplot variables getter and setter
%

\newcommand{\gpsetvar}[2]{%
  \expandafter\xdef\csname gp@var@#1\endcsname{#2}
}

\newcommand{\gpgetvar}[1]{%
  \csname gp@var@#1\endcsname %
}

%
% some wrapper code
%

% short for the lengthy xcolor rgb definition
\newcommand*\gprgb[3]{rgb,1000:red,#1;green,#2;blue,#3}

% short for a filled path
\newcommand*\gpfill[1]{\path[fill,#1]}

% short for changing the linewidth
\newcommand*\gpsetlinewidth[1]{\pgfsetlinewidth{#1\gpbaselw}}

\newcommand*\gpsetlinetype[1]{\tikzstyle{gp path}=[#1]}

% short for changing the pointsize
\newcommand*\gpsetpointsize[1]{\tikzstyle{gp point}=[mark size=#1\gpbasems]}

% prevent plot mark distortions due to changes in the PGF transformation matrix
% use `\gpscalepointstrue' and `\gpscalepointsfalse' for enabling and disabling
% point scaling
%
\newif\ifgpscalepoints
\newcommand*\gppoint[2]{%
\ifgpscalepoints%
  \path[solid] plot[only marks,gp point,#1] coordinates {#2};%
\else%
  \node[anchor=center,inner sep=0pt,outer sep=0pt] at #2 {\tikz{\path[solid] plot[only marks,gp point,#1] coordinates {(0,0)};}};%
\fi}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%  You may want to adapt the following to fit your needs
%%  in you individual style file and/or within your document.
%%

%
% style for every plot
%
\tikzstyle{gnuplot}=[%
  >=stealth',%
  cap=round,%
  join=round,%
  set style = {%
    {every node} = [%
      font=\small%
    ]%
  }
]

\tikzstyle{gp node left}=[anchor=mid west,yshift=-.12ex]
\tikzstyle{gp node center}=[anchor=mid,yshift=-.12ex]
\tikzstyle{gp node right}=[anchor=mid east,yshift=-.12ex]

% basic plot mark size (points)
\newlength{\gpbasems}
\setlength{\gpbasems}{.4pt}

% basic linewidth
\newlength{\gpbaselw}
\setlength{\gpbaselw}{.4pt}

% this is the default color for pattern backgrounds
\colorlet{gpbgfillcolor}{white}


% this should reverse the normal text node presets, for the
% later referencing as described below
\tikzstyle{gp refnode}=[coordinate,yshift=.12ex]

% to add an empty label with the referenceable name "my node"
% to the plot, just add the following line to your gnuplot
% file:
%
% set label "" at 1,1 font ",gp refnode,name=my node"
%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%  The following TikZ-styles are derived from the 'pgf.styles.*' tables
%%  in the Lua script.
%%  To change the number of used styles you should change them there and
%%  regenerate this style file.
%%

]])
  f:write("% plotmark settings\n")
  for i = 1, #pgf.styles.plotmarks do
    f:write("\\tikzstyle{"..pgf.styles.plotmarks[i][1].."} = ["..pgf.styles.plotmarks[i][2].."]\n")
  end
  f:write("\n% pattern settings\n")
  for i = 1, #pgf.styles.patterns do
    f:write("\\tikzstyle{"..pgf.styles.patterns[i][1].."} = ["..pgf.styles.patterns[i][2].."]\n")
  end
  f:write("\n% if the 'tikzplot' option is used the corresponding lines will be smoothed by default\n")
  for i = 1, #pgf.styles.plotstyles do
    f:write("\\tikzstyle{"..pgf.styles.plotstyles[i][1].."} = ["..pgf.styles.plotstyles[i][2].."]%\n")
  end
  -- line styles for borders etc ...
  f:write("\n% linestyle settings\n")
  for i = 1, 3 do
    f:write("\\tikzstyle{"..pgf.styles.linetypes[i][1].."} = ["..pgf.styles.linetypes[i][2].."]\n")
  end
  f:write("\n% linestyle color settings\n")
  for i = 1, 3 do
    f:write("\\colorlet{"..pgf.styles.lt_colors[i][1].."}{"..pgf.styles.lt_colors[i][2].."}\n")
  end
  -- line styles for the plots
  f:write("\n% command for switching to dashed lines\n")
  f:write("\\newcommand{\\gpdashedlines}{%\n")
  for i = 4, #pgf.styles.linetypes do
    f:write("  \\tikzstyle{"..pgf.styles.linetypes[i][1].."} = ["..pgf.styles.linetypes[i][2].."]%\n")
  end
  f:write("}\n")
  f:write("\n% command for switching to colored lines\n")
  f:write("\\newcommand{\\gpcoloredlines}{%\n")
  for i = 4, #pgf.styles.lt_colors do
    f:write("  \\colorlet{"..pgf.styles.lt_colors[i][1].."}{"..pgf.styles.lt_colors[i][2].."}%\n")
  end
  f:write("}\n")
  f:write("\n% command for switching to solid lines\n")
  f:write("\\newcommand{\\gpsolidlines}{%\n")
  for i = 4, #pgf.styles.linetypes do
    f:write("  \\tikzstyle{"..pgf.styles.linetypes[i][1].."} = [solid]%\n")
  end
  f:write("}\n")
  f:write("\n% command for switching to monochrome (black) lines\n")
  f:write("\\newcommand{\\gpmonochromelines}{%\n")
  for i = 4, #pgf.styles.lt_colors do
    f:write("  \\colorlet{"..pgf.styles.lt_colors[i][1].."}{black}%\n")
  end
  f:write("}\n\n")
  f:write([[
%
% some initialisations
%
% by default all lines will be colored and dashed
\gpcoloredlines
\gpdashedlines
\gpsetpointsize{4}
\gpsetlinetype{gp_lt_solid}
\gpscalepointsfalse
\endinput
]])
  f:close()
end


pgf.print_help = function(fwrite)

  -- got a segfault on Windows (actually Wine) if the string size
  -- exceeds ca. 1K, strange :-(
  fwrite([[
  additional terminal options:

    {help}
    {monochrome}
    {solid}
    {originreset}
    {gparrows}
    {gppoints}
    {nopicenvironment}
    {size <x>{unit},<y>{unit}}
    {scale <x>,<y>}
    {plotsize <x>{unit},<y>{unit}}
    {font "<fontdesc>"}
    {createstyle}
    {fulldoc}
    {preamble "<preamble_string>"}
    {tikzplot <ltn>,...}
    {providevars <var name>,...}

  For all options that expect lengths as their arguments they
  will default to `cm' if no unit is specified. For all lengths
  the following units my be used: 'cm', 'mm', 'in' or 'inch',
  'pt', 'pc', 'bp', 'dd', 'cc'. Spaces between numbers and units
  are not allowed.
  
  `monochrome' disables line coloring and switches to grayscaled
  fills.
  
  `solid' use only solid lines.

]]) 

  fwrite([[
  `originreset' moves the origin of the TikZ picture to the lower
  left corner of the plot. It may be used to align several plots
  within one tikzpicture environment. This is not tested with
  multiplots and pm3d plots!

  `gparrows' use gnuplot's internal arrow drawing function
  instead of the ones provided by TikZ.
  
  `gppoints' use gnuplot's internal plotmark drawing function
  instead of the ones provided by TikZ.
  
  `nopicenvironment' omits the declaration of the 'tikzpicture'
  environment in order to set it manually. This permits putting
  some PGF/TikZ code directly before or after the plot.
  
]]) 

  fwrite([[
  The `size' option expects two lenghts <x> and <y> as the canvas size.
  The default size of the canvas is 10cm x 10cm.
  
  The `scale' option works similar to the `size' option but expects
  scaling factors <x> and <y> instead of lengths.
  
  The `plotsize' option permits setting the size of the plot area
  instead of the canvas size, which is the usual gnuplot behaviour.
  Using this option may lead to slightly asymmetric tic lengths.
  Like `originreset' this option may not lead to convenient results
  if used with multiplots or pm3d plots.

  `createstyle' derives the LaTeX style file from the script and
  writes it to the file `]]..pgf.LATEX_STYLE_FILE..'.sty'..[['.

  `fulldoc' produces a full LaTeX document for direct compilation.
  
  <preamble_string> in conjunction with `fulldoc' may contain any
  valid LaTeX code to be put in the document preamble.

]])

  fwrite([[
  With the `tikzplot' options the '\path plot' command will be used
  instead of only '\path'. The following list of numbers of linetypes
  (<ltn>,...) defines the affected plotlines. There exists a plotstyle
  for every linetype. The default plotstyle is 'smooth' for every
  linetype >= 1.
  
  The `providevars' options makes gnuplot's internal and user variables
  available by using the '\gpgetvar{<var name>}' commmand within the TeX
  script. Use gnuplot's 'show variables all' command to see the list
  of valid variables.
  
  <fontdesc> may contain any valid LaTeX font commands like e.g.
  `\small'. This can be `misused' to add further code to a node,
  e.g. '\small,yshift=1ex' or ',yshift=1ex' are also valid while
  the latter does not change the current font settings.
  
  Strings have to be put in single or double quotes. Double quoted
  strings may contain special characters like newlines `\n' etc.
  
]])
end


--[[===============================================================================================

  gfx.* helper functions
  
  Main intention is to prevent redundancies in the drawing
  operations and keep the pgf.* API as consistent as possible.
  
]]--===============================================================================================

gfx.inline = false

gfx.path = {}
gfx.posx = nil
gfx.posy = nil

-- default canvas scales to 10cm (fix)
gfx.DEFAULT_CANVAS_SIZE = 10


-- gfx.DEFAULT_LINE_TYPE = -2
-- gfx.linetype_idx = gfx.DEFAULT_LINE_TYPE -- current linetype intended for the plot
gfx.linetype_idx = nil       -- current linetype intended for the plot
gfx.linetype_idx_set = nil   -- current linetype set in the plot
gfx.linewidth = nil
gfx.linewidth_set = nil

-- internal calculated scaling factors
gfx.scalex = 1
gfx.scaley = 1

-- recalculate the origin of the plot
-- used for moving the origin to the lower left
-- corner...
gfx.origin_xoffset = 0
gfx.origin_yoffset = 0



-- color set in the document
gfx.color = ''
gfx.color_set = ''

gfx.pointsize = nil
gfx.pointsize_set = nil

gfx.text_font = ''
gfx.text_justify = "center"
gfx.text_angle = 0

-- option vars
gfx.opt = {
  latex_preamble = '',
  default_font = '',
  xscale_factor = 1,
  yscale_factor = 1,
  lines_dashed = true,
  lines_colored = true,
  -- use gnuplot arrows or points instead of TikZ?
  gp_arrows = false,
  gp_points = false,
  -- don't put graphic commands into a tikzpicture environment
  nopicenv = false,
  -- produce full LaTeX document?
  full_doc = false,
  -- in gnuplot all sizes refer to the size of the canvas
  -- and not the size of plot itself
  plotsize_x = nil,
  plotsize_y = nil,
  set_plotsize = false,
  -- recalculate the origin of the plot
  -- used for moving the origin to the lower left
  -- corner...
  set_origin = false,
  -- list of _linetypes_ of plots that should be drawn as with the \plot
  -- command instead of \path
  plot_list = {},
  -- uses some pdf/ps specials with image function that will only work
  -- with pdf/ps generation!
  direct_image = true,
  -- list of gnuplot variables that should be made available via
  -- \gpsetvar{name}{val}
  gnuplot_vars = {}
}

-- within tikzpicture environment or not
gfx.in_picture = false

-- have not determined the plotbox, see the 'plotsize' option
gfx.have_plotbox = false

gfx.current_boundingbox = {
  xleft = nil, xright = nil, ytop = nil, ybot = nil
}
-- plot bounding boxes counter
gfx.boundingbox_cnt = 0

gfx.TEXT_ANCHOR = {
    ["left"]   = "gp node left",
    ["center"] = "gp node center",
    ["right"]  = "gp node right"
}

gfx.HEAD_STR = {"", "->", "<-", "<->"}


gfx.check_boundingbox = function(change_plot)
  local t = gp.get_boundingbox()
  local k,v
  if change_plot then
    if gfx.opt.set_origin then
      -- move origin to the lower left corner of the plot
      gfx.origin_xoffset = - t.xleft
      gfx.origin_yoffset = - t.ybot
    end
    if gfx.opt.set_plotsize then
      if (t.xright - t.xleft) > 0 then
        gfx.scalex = gfx.scalex*(gfx.opt.plotsize_x*term.xmax/gfx.DEFAULT_CANVAS_SIZE)/(t.xright - t.xleft)
        gfx.scaley = gfx.scaley*(gfx.opt.plotsize_y*term.ymax/gfx.DEFAULT_CANVAS_SIZE)/(t.ytop - t.ybot)
      else
        -- could not determin a valid bounding box, so we scale the
        -- whole canvas to prevent totally flawed plots
        gfx.scalex = gfx.scalex*gfx.opt.plotsize_x/gfx.DEFAULT_CANVAS_SIZE
        gfx.scaley = gfx.scaley*gfx.opt.plotsize_y/gfx.DEFAULT_CANVAS_SIZE
      end
    end
  else
    for k, v in pairs (t) do
      if v ~= gfx.current_boundingbox[k] then
        gfx.boundingbox_cnt = gfx.boundingbox_cnt + 1
        gfx.current_boundingbox = t
        pgf.write_boundingbox(t, gfx.boundingbox_cnt)
        break
      end  
    end
  end
end

gfx.check_variables = function()
  local vl = gfx.opt.gnuplot_vars
  local t = gp.get_all_variables()
  local sl = {}
  for i=1,#vl do
    if t[vl[i]] then
      sl[vl[i]] = t[vl[i]][3]
      if not t[vl[i]][4] == nil then
        sl[vl[i].." Im"] = t[vl[i]][4]
      end
    end
  end
  pgf.write_variables(sl)
end

-- boundingbox data is available with the first
-- drawing command, so this function should not
-- be called earlier
gfx.check_plotbox = function()
  if not gfx.have_plotbox and gfx.in_picture then
    gfx.check_boundingbox(true)
    gfx.have_plotbox = true    
  end
end


-- do we have to start a new path?
gfx.check_inline = function()
  gfx.check_plotbox()
  if gfx.inline == true then
    pgf.draw_path(gfx.path)
    gfx.inline = false
    gfx.path = {}
    gfx.posx = nil
    gfx.posy = nil
  end
end

-- did the linetype change?
gfx.check_linetype = function()
  if gfx.linetype_idx ~= gfx.linetype_idx_set then
    local lt = ((gfx.linetype_idx+3) % #pgf.styles.linetypes)+1
    pgf.set_linetype(pgf.styles.linetypes[lt][1])
    gfx.linetype_idx_set = gfx.linetype_idx
  end
end

-- did the color change?
gfx.check_color = function()
  if gfx.color_set ~= gfx.color then
    pgf.set_color(gfx.color)
    gfx.color_set = gfx.color
  end
end

-- sanity check if we already are at this position in our path
-- and save this position
gfx.check_coord = function(x, y)
  if x == gfx.posx and y == gfx.posy then
    return true
  end
  gfx.posx = x
  gfx.posy = y
  return false
end

-- did the linewidth change?
gfx.check_linewidth = function()
  if gfx.linewidth ~= gfx.linewidth_set then
    pgf.set_linewidth(gfx.linewidth)
    gfx.linewidth_set = gfx.linewidth
  end
end

-- did the pointsize change?
gfx.check_pointsize = function()
  if gfx.pointsize ~= gfx.pointsize_set then
    pgf.set_pointsize(gfx.pointsize)
    gfx.pointsize_set = gfx.pointsize
  end
end


gfx.startline = function(x, y)
  gfx.check_color()
  gfx.check_linetype()
  gfx.check_linewidth()

  --  init path with first coords
  gfx.path = {{x,y}}  
  gfx.inline = true
end

-- type  string  LT|RGB|GRAY
-- val   table   {name}|{r,g,b}
gfx.format_color = function(type, val)
  local c
  if type == 'LT' then
    c = pgf.styles.lt_colors[((val[1]+3) % #pgf.styles.lt_colors) + 1][1]
  elseif type == 'RGB' then
    c = string.format("\\gprgb{%i}{%i}{%i}",
                  val[1]*1000.5, val[2]*1000.5, val[3]*1000.5)
  elseif type == 'GRAY' then
    c = string.format("black!%i", val[1]*101)
  end
  return c
end

gfx.set_color = function(type, val)
  gfx.color = gfx.format_color(type, val)
end



--[[===============================================================================================

  The terminal layer

]]--===============================================================================================


--
-- initial = 1  for the initial "set term" call
--           0  for subsequent option changes -- currently unused, since the changeable options
--              are hardcoded within gnuplot :-(
--
-- t_count   see e.g. int_error()
--
term.options = function(opt_str, initial, t_count)

  local next = ""
  local type = nil
  local s_start, s_end = 1, 1
  local opt_len = string.len(opt_str)
  
  t_count = t_count - 1

  local almost_equals = function(param, opt)
    local op1, op2
  
    local st, _ = string.find(opt, "$", 2, true)
    if st then
      op1 = string.sub(opt, 1, st-1)
      op2 = string.sub(opt, st+1)
      if (string.sub(param, 1, st-1) == op1)
          and (string.find(op1..op2, param, 1, true) == 1) then
        return true
      end
    elseif opt == param then
      return true
    end
    return false
  end

  --
  -- simple parser for options and strings
  --
  local get_next_token = function()
    
    -- beyond the limit?
    if s_start > opt_len then
      next = ""
      type = nil
      return
    end
    
    t_count = t_count + 1
    
    -- search the start of the next token
    s_start, _ = string.find (opt_str, '[^%s]', s_start)
    if not s_start then
      next = ""
      type = nil
      return
    end

    -- a new string argument?
    local next_char = string.sub(opt_str, s_start, s_start)
    if next_char == '"' or next_char == "'" then
      -- find the end of the string by searching for
      -- the next not escaped quote
      _ , s_end = string.find (opt_str, '[^\\]'..next_char, s_start+1)
      if s_end then
        next = string.sub(opt_str, s_start+1, s_end-1)
        if next_char == '"' then
          -- Wow! this is to resolve all string escapes, kind of "unescape string"
          next = assert(loadstring("return(\""..next.."\")"))()
        end
        type = "string"
      else
        -- FIXME: error: string does not end...
        -- seems that gnuplot adds missing quotes
        -- so this will never happen...
      end
    else
      -- ok, it's not a string...
      -- then find the next white space or end of line
      -- comma separated strings are regarded as one token
      s_end, _ = string.find (opt_str, '[^,][%s]+[^,]', s_start+1)
      if not s_end then -- reached the end of the string
        s_end = opt_len + 1
      else
        s_end = s_end + 1
      end
      next = string.sub(opt_str, s_start, s_end-1)
      type = "op"
    end
    s_start = s_end + 1
    return
  end    

  -- from the Lua wiki
  local explode = function(div,str)
    if (div=='') then return false end
    local pos,arr = 0,{}
    local trim = function(s) return (string.gsub(s,"^%s*(.-)%s*$", "%1")) end
    -- for each divider found
    for st,sp in function() return string.find(str,div,pos,true) end do
      table.insert(arr, trim(string.sub(str,pos,st-1))) -- Attach chars left of current divider
      pos = sp + 1 -- Jump past current divider
    end
    table.insert(arr, trim(string.sub(str,pos))) -- Attach chars right of last divider
    return arr
  end

  -- conversion factors in `cm'
  local units = {
    ['']    = 1,        -- default
    ['cm']  = 1,
    ['mm']  = 0.1,
    ['in']  = 2.54,
    ['inch']= 2.54,
    ['pt']  = 0.035146, -- Pica Point   (72.27pt = 1in)
    ['pc']  = 0.42176,  -- Pica         (1 Pica = 1/6 inch)
    ['bp']  = 0.035278, -- Big Point    (72bp = 1in)
    ['dd']  = 0.0376,   -- Didot Point  (1cm = 26.6dd)
    ['cc']  = 0.45113   -- Cicero       (1cc = 12 dd)
  }

  local calc_unit = function (str)
    local num, unit = string.match(str, '([%d%.]+)([a-z]*)')
    local factor = units[unit]
    num = tonumber(num)
    if num and factor then
      return num*factor
    else
      return false
    end
  end

  local get_two_numbers = function(str)
    local args = explode(',', str)
    local num1, num2
    if #args ~= 2 then
      return false, nil
    else
      num1 = calc_unit(args[1])
      num2 = calc_unit(args[2])
      if not (num1 or num2) then
        return false, nil
      end
    end
    return num1, num2
  end
  
  local print_help = false

  while true do
    get_next_token()
    if not type then break end
    if almost_equals(next, "script") then
      get_next_token()
      -- nothing yet
    elseif almost_equals(next, "he$lp") then
      print_help = true
    elseif almost_equals(next, "mono$chrome") then
      -- no colored lines
      gfx.opt.lines_colored = false
    elseif almost_equals(next, "so$lid") then
      -- no dashed and dotted etc. lines
      gfx.opt.lines_dashed = false
    elseif almost_equals(next, "gparr$ows") then
      -- use gnuplot arrows instead of TikZ
      gfx.opt.gp_arrows = true
    elseif almost_equals(next, "gppoint$s") then
      -- use gnuplot points instead of TikZ
      gfx.opt.gp_points = true
    elseif almost_equals(next, "nopic$environment") then
      -- omit the 'tikzpicture' environment
      gfx.opt.nopicenv = true
    elseif almost_equals(next, "origin$reset") then
      -- moves the origin of the TikZ picture to the lower left corner of the plot
      gfx.opt.set_origin = true
    elseif almost_equals(next, "plot$size") then
      get_next_token()
      gfx.opt.plotsize_x, gfx.opt.plotsize_y = get_two_numbers(next)
      if not (gfx.opt.plotsize_x) then
        gp.int_error(t_count, string.format("error: two comma seperated lengths expected, got `%s'.", next))
      end
      gfx.opt.set_plotsize = true
      -- since gnuplot does not support this we are trying keep at least some
      -- aspect ratios, assuming that the actual scaling will not differ much
      local xratio = gfx.DEFAULT_CANVAS_SIZE/gfx.opt.plotsize_x
      local yratio = gfx.DEFAULT_CANVAS_SIZE/gfx.opt.plotsize_y
      term.h_tic = term.h_tic*xratio
      term.v_tic = term.v_tic*yratio
      term.h_char = term.h_char*xratio
      term.v_char = term.v_char*yratio
    elseif almost_equals(next, "si$ze") then
      get_next_token()
      local plotsize_x, plotsize_y = get_two_numbers(next)
      if not (plotsize_x) then
        gp.int_error(t_count, string.format("error: two comma seperated lengths expected, got `%s'.", next))
      end
      gfx.opt.xscale_factor = plotsize_x/gfx.DEFAULT_CANVAS_SIZE
      gfx.opt.yscale_factor = plotsize_y/gfx.DEFAULT_CANVAS_SIZE
      term.xmax = term.xmax * gfx.opt.xscale_factor
      term.ymax = term.ymax * gfx.opt.yscale_factor
    elseif almost_equals(next, "sc$ale") then
      get_next_token()
      gfx.opt.xscale_factor, gfx.opt.yscale_factor = get_two_numbers(next)
      if not (gfx.opt.xscale_factor) then
        gp.int_error(t_count, string.format("error: two comma seperated numbers expected, got `%s'.", next))
      end
      term.xmax = term.xmax * gfx.opt.xscale_factor
      term.ymax = term.ymax * gfx.opt.yscale_factor
    elseif almost_equals(next, "tikzpl$ot") then
      get_next_token()
      local args = explode(',', next)
      for i = 1,#args do
        args[i] = tonumber(args[i])
        if args[i] == nil then
          gp.int_error(t_count, string.format("error: list of comma seperated numbers expected, got `%s'.", next))
        end
        args[i] = args[i] - 1
      end
      gfx.opt.plot_list = args
    elseif almost_equals(next, "provide$vars") then
      get_next_token()
      local args = explode(',', next)
      gfx.opt.gnuplot_vars = args
    elseif almost_equals(next, "full$doc") then
      -- produce full tex document
      gfx.opt.full_doc = true
    elseif almost_equals(next, "create$style") then
      -- creates the coresponding LaTeX style from the script
      local f = io.open(pgf.LATEX_STYLE_FILE..".sty" , "w+")
      pgf.create_style(f)
    elseif almost_equals(next, "fo$nt") then
      get_next_token()
      if type == 'string' then
        gfx.opt.default_font = next
      else
        gp.int_error(t_count, string.format("error: string expected, got `%s'.", next))
      end
    elseif almost_equals(next, "pre$amble") then
      get_next_token()
      if type == 'string' then
        gfx.opt.latex_preamble = gfx.opt.latex_preamble .. next .. "\n"
      else
        gp.int_error(t_count, string.format("error: string expected, got `%s'.", next))
      end
    else
      gp.int_warn(t_count, string.format("unknown option `%s'.", next))
    end
  end

  if print_help then
    pgf.print_help(gp.term_out)
  end

  return 1
end

-- Called once, when the device is first selected.
term.init = function()
  if gfx.opt.full_doc then
    pgf.doc_begin(gfx.opt.latex_preamble)
  end
  return 1
end

-- Called just before a plot is going to be displayed.
term.graphics = function()
  -- nothing set yet
  gfx.linetype_idx_set = nil
  gfx.linewidth_set = nil
  gfx.pointsize_set = nil
  gfx.color_set = nil
  
    -- put a newline between subsequent plots in fulldoc mode...
  if gfx.opt.full_doc then
    gp.write("\n")
  end
  pgf.graph_begin(gfx.opt.default_font, gfx.opt.nopicenv)
  gfx.scalex = gfx.opt.xscale_factor*gfx.DEFAULT_CANVAS_SIZE/term.xmax
  gfx.scaley = gfx.opt.yscale_factor*gfx.DEFAULT_CANVAS_SIZE/term.ymax
  gfx.in_picture = true
  return 1
end


term.vector = function(x, y)
  if not gfx.inline then
    gfx.startline(gfx.posx, gfx.posy)
  end
  -- check for zero path length and add the path coords to gfx.path
  if not gfx.check_coord(x, y) then
    gfx.path[#gfx.path+1] = {x,y}
  end
  return 1
end

term.move = function(x, y)
  -- if we move to our last position we will just continue the path there
  if not gfx.check_coord(x, y) then
    gfx.check_inline()
    gfx.startline(x, y)
  end
  return 1
end

term.linetype = function(type)
  gfx.check_inline()

  gfx.set_color('LT', {type})
  
  gfx.linetype_idx = type

  return 1
end

term.point = function(x, y, num)
  if gfx.opt.gp_points then
    return 0
  else
    gfx.check_inline()
    gfx.check_color()
    gfx.check_linewidth()
    gfx.check_pointsize()
  
    local pm
    if num == -1 then
      pm = pgf.styles.plotmarks[1][1]
    else
      pm = pgf.styles.plotmarks[(num % (#pgf.styles.plotmarks-1)) + 2][1]
    end
    pgf.draw_points({{x,y}}, pm)
    
    return 1
  end
end


--[[
  this differs from the original API
  one may use the additional parameters to define own styles
  e.g. "misuse" angle for numbering predefined styles...

  int length        /* head length */
  double angle      /* head angle in degrees */
  double backangle  /* head back angle in degrees */
  int filled        /* arrow head filled or not */
]]
term.arrow = function(sx, sy, ex, ey, head, length, angle, backangle, filled)
  if gfx.opt.gp_arrows then
    return 0
  else
    gfx.check_inline()
    gfx.check_color()
    gfx.check_linetype()
    gfx.check_linewidth()
    pgf.draw_arrow({{sx,sy},{ex,ey}}, gfx.HEAD_STR[head+1], 0)
    return 1
  end
end

-- Called immediately after a plot is displayed.
term.text = function()
  gfx.check_inline()
  pgf.graph_end(gfx.opt.nopicenv)
  gfx.in_picture = false
  return 1
end

term.put_text = function(x, y, txt)
  gfx.check_inline()
  gfx.check_color()
  
  pgf.draw_text({x, y}, txt, gfx.text_angle, gfx.TEXT_ANCHOR[gfx.text_justify], gfx.text_font)
  
  return 1
end

term.justify_text = function(justify)
  gfx.text_justify = justify
  return 1
end

term.text_angle = function(ang)
  gfx.text_angle = ang
  return 1
end

term.linewidth = function(width)
  if gfx.linewidth ~= width then
    gfx.linewidth = width
    gfx.check_inline()
  end
  return 1
end

term.pointsize = function(size)
  if gfx.pointsize ~= size then
    gfx.pointsize = size
    gfx.check_inline()
  end
  return 1
end

term.set_font = function(font)
  gfx.text_font = font
  return 1
end

-- at the moment this is only used to check
-- the plot's bounding box as seldom as possible
term.layer = function(l)
  if l == 'end_text' then
    -- called after a plot is finished (also after each "mutiplot")
    gfx.check_boundingbox(false)
  end
  return 1
end

-- we don't use this, because we are implicitly testing
-- for closed paths
term.path = function(p)
  return 1
end


term.filled_polygon = function(style, fillpar, t)
  local pattern = nil
  local color = nil
  local opacity = 100
  local saturation = 100
  
  gfx.check_inline()

  if style == 'EMPTY' then
      -- FIXME: should be the "background color" and not gpbgfillcolor
      pattern = ''
      color = 'gpbgfillcolor'
      saturation = 100
      opacity = 100
  elseif style == 'DEFAULT' or style == 'OPAQUE' then -- FIXME: not shure about the opaque style
      pattern = ''
      color = gfx.color
      saturation = 100
      opacity = 100
  elseif style == 'SOLID' then
      pattern = ''
      color = gfx.color
      if fillpar < 100 then
        saturation = fillpar
      else
        saturation = 100
      end
      opacity = 100
  elseif style == 'PATTERN' then
      pattern = pgf.styles.patterns[(fillpar % #pgf.styles.patterns) + 1][1]
      color = gfx.color
      saturation = 100
      opacity = 100
  elseif style == 'TRANSPARENT_SOLID' then
      pattern = ''
      color = gfx.color
      saturation = 100
      opacity = fillpar
  elseif style == 'TRANSPARENT_PATTERN' then
      pattern = pgf.styles.patterns[(fillpar % #pgf.styles.patterns) + 1][1]
      color = gfx.color
      saturation = 100
      opacity = 0
  end
  
  pgf.draw_fill(t, pattern, color, saturation, opacity)  
  
  return 1
end


term.boxfill = function(style, fillpar, x1, y1, width, height)
  local t = {{x1, y1}, {x1+width, y1}, {x1+width, y1+height}, {x1, y1+height}}
  return term.filled_polygon(style, fillpar, t)
end

-- points[row][column]
-- m: #cols, n: #rows
-- corners: clip box and draw box coordinates
-- ctype: "RGB" or "GRAY" (unused since we allways use RGB to keep things simple)
term.image = function(m, n, points, corners, ctype)
  gfx.check_inline()
  
  pgf.start_clipbox({corners[3][1],corners[3][2]},{corners[4][1],corners[4][2]})
  
  if gfx.opt.direct_image then
    local ll = {corners[1][1],corners[2][2]}
    local ur = {corners[2][1],corners[1][2]}
    pgf.raw_rgb_image(points, m, n, ll, ur)
  else
    local w = (corners[2][1] - corners[1][1])/m
    local h = (corners[1][2] - corners[2][2])/n

    local yy,yyy,xx,xxx
    for cnt = 1,#points do
      xx = corners[1][1]+(cnt%m-1)*w
      yy = corners[1][2]-math.floor(cnt/m)*h
      yyy = yy-h
      xxx = xx+w
      pgf.draw_fill({{xx, yy}, {xxx, yy}, {xxx, yyy}, {xx, yyy}}, '', gfx.format_color('RGB', points[cnt]) , 100, 100)
    end
  end
  pgf.end_clipbox()
end

term.make_palette = function()
  -- continuous number of colours
  return 0
end

term.previous_palette = function()
  return 1
end

term.set_color = function(type, lt, value, r, g, b)
  gfx.check_inline()
  -- FIXME gryscale on monochrome?? ... or use xcolor?

  if type == 'LT' then
    gfx.set_color('LT', {lt})
  elseif type == 'FRAC' then
    if gfx.opt.lines_colored then
      gfx.set_color('RGB', {r, g , b})
    else
      gfx.set_color('GRAY', {value})
    end
  elseif type == 'RGB' then
    gfx.set_color('RGB', {r, g , b})
  else
    gp.int_error(string.format("set color: unknown type (%s), lt (%i), value (%.3f)\n", type, lt, value))
  end
  
  return 1
end

-- Called when gnuplot is exited.
term.reset = function(p)
  gfx.check_inline()
  gfx.check_variables()
  if gfx.opt.full_doc then
    pgf.doc_end()
  end
  return 1
end

--[[===============================================================================================

  command line code

]]--===============================================================================================

if arg then -- called from the command line!
  if #arg > 0 and arg[1] == 'style' then
    -- write style file
    local f = io.open(pgf.LATEX_STYLE_FILE..".sty" , "w+")
    pgf.create_style(f)
  else
    io.write([[
  This script is intended to be called from GNUPLOT.
  
  For generating the associated LaTeX style file
  (']] .. pgf.LATEX_STYLE_FILE..".sty')" .. [[ just call this script
  with the additional option 'style':
    
    # lua gnuplot.lua style
  
  From GNUPLOT you may call this script with some
]])
    pgf.print_help(io.write)
  end
end
