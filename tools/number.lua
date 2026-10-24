-- Pandoc filter used by tools/tex2md.py.
--
-- Numbers chapters, sections, figures, tables, equations and theorems the
-- way the PDF does (Figure 3.1, equation (4.6a), appendix A, ...), resolves
-- \ref/\eqref links to those numbers, and rewrites figures and equations
-- into plain GFM so GitHub renders the math in captions.
-- Each chapter heading is preceded by "<!-- chapter: N -->" so tex2md.py
-- can split the output into one file per chapter.

local LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

local numbers = {}     -- label -> number string
local referenced = {}  -- labels that some \ref/\eqref points to

local appendix = false
local chapter = 0
local chap = ""        -- "3", "A", or "" in unnumbered chapters
local sec, subsec = 0, 0
local fig, tab, eq = 0, 0, 0
local thm = {}
local table_label = nil  -- label of the table about to be visited

local function anchor(id)
  return pandoc.RawInline("html", '<a id="' .. id .. '"></a>')
end

local function prefixed(n)
  if chap == "" then return tostring(n) end
  return chap .. "." .. n
end

-- Split an align body on top-level "\\" (not inside braces or nested
-- environments such as array).
local function split_rows(body)
  local rows, depth, start, i = {}, 0, 1, 1
  while i <= #body do
    local c = body:sub(i, i)
    if c == "{" then
      depth = depth + 1
    elseif c == "}" then
      depth = depth - 1
    elseif body:sub(i, i + 6) == "\\begin{" then
      depth = depth + 1
      i = i + 5  -- the "{" after \begin is counted on the next step
    elseif body:sub(i, i + 4) == "\\end{" then
      depth = depth - 1
      i = i + 3
    elseif c == "\\" and body:sub(i + 1, i + 1) == "\\" and depth == 0 then
      table.insert(rows, body:sub(start, i - 1))
      start = i + 2
      i = i + 1
    end
    i = i + 1
  end
  table.insert(rows, body:sub(start))
  return rows
end

local function take_labels(s, n, ids)
  for label in s:gmatch("\\label{([^}]*)}") do
    numbers[label] = n
    table.insert(ids, label)
  end
  return (s:gsub("%s*\\label{[^}]*}", ""))
end

-- Returns the numbered math text and the labels defined in it.
local function number_math(text)
  local ids = {}
  local parent = text:match("^%s*\\label{([^}]*)}%s*\\begin{align}")
  local env, body = text:match("\\begin{(align)}(.*)\\end{align}")
  if not env then
    env, body = text:match("^%s*\\begin{(equation)}(.*)\\end{equation}%s*$")
  end
  if env == "equation" then
    eq = eq + 1
    local n = prefixed(eq)
    body = take_labels(body, n, ids)
    return "\\begin{equation}" .. body .. " \\tag{" .. n .. "}\n\\end{equation}", ids
  elseif env == "align" then
    local base, sub = nil, 0
    if parent then
      -- \begin{subequations}: rows are (N a), (N b), ...
      eq = eq + 1
      base = prefixed(eq)
      numbers[parent] = base
      table.insert(ids, parent)
    end
    local rows = split_rows(body)
    for k, row in ipairs(rows) do
      if not row:match("\\nonumber") and not row:match("\\notag") and row:match("%S") then
        local n
        if base then
          sub = sub + 1
          n = base .. LETTERS:sub(sub, sub):lower()
        else
          eq = eq + 1
          n = prefixed(eq)
        end
        rows[k] = take_labels(row, n, ids) .. " \\tag{" .. n .. "}"
      end
    end
    return "\\begin{align}" .. table.concat(rows, "\\\\") .. "\\end{align}", ids
  end
  return (text:gsub("%s*\\label{[^}]*}", "")), ids
end

-- Pass 1: collect which labels are referenced, so only those get anchors.
local collect = {
  Link = function(l)
    local ref = l.attributes["reference"]
    if ref then referenced[ref] = true end
  end,
}

-- Pass 2: number everything, in document order.
local number = {
  traverse = "topdown",

  Para = function(p)
    if #p.content == 1 and p.content[1].text == "APPENDIXMARKER" then
      appendix = true
      chapter = 0
      return {}
    end
  end,

  Header = function(h)
    local num
    local unnumbered = h.classes:includes("unnumbered")
    if h.level == 1 then
      if unnumbered then
        chap = ""
      else
        chapter = chapter + 1
        chap = appendix and LETTERS:sub(chapter, chapter) or tostring(chapter)
        num = chap
      end
      sec, subsec, fig, tab, eq, thm = 0, 0, 0, 0, 0, {}
    elseif chap ~= "" and not unnumbered and h.level == 2 then
      sec, subsec, thm = sec + 1, 0, {}
      num = chap .. "." .. sec
    elseif chap ~= "" and not unnumbered and h.level == 3 then
      subsec = subsec + 1
      num = chap .. "." .. sec .. "." .. subsec
    end
    if num then
      numbers[h.identifier] = num
      h.content:insert(1, pandoc.Space())
      h.content:insert(1, pandoc.Str(num))
    end
    if referenced[h.identifier] then
      h.content:insert(1, anchor(h.identifier))
    end
    if h.level == 1 then
      return { pandoc.RawBlock("html", "<!-- chapter: " .. (num or "") .. " -->"), h }
    end
    return h
  end,

  Figure = function(f)
    fig = fig + 1
    local n = prefixed(fig)
    numbers[f.identifier] = n
    local images = {}
    local sublabels = {}
    local k = 0
    pandoc.walk_block(f, {
      Span = function(s)
        -- a \label after a subfloat's image, e.g. fig:noDAC -> 7.7b
        if s.identifier ~= "" then
          numbers[s.identifier] = n .. LETTERS:sub(k, k):lower()
          table.insert(sublabels, s.identifier)
        end
      end,
      Image = function(img)
        k = k + 1
        img.identifier = ""
        img.attributes = {}
        img.caption = { pandoc.Str("Figure " .. n) }
        table.insert(images, img)
        table.insert(images, pandoc.Space())
      end,
    })
    local caption = pandoc.utils.blocks_to_inlines(f.caption.long)
    caption:insert(1, pandoc.Strong { pandoc.Str("Figure " .. n .. ":") })
    caption:insert(2, pandoc.Space())
    local anchors = { anchor(f.identifier) }
    for _, id in ipairs(sublabels) do table.insert(anchors, anchor(id)) end
    return {
      pandoc.Para(anchors),
      pandoc.Para(images),
      pandoc.Para { pandoc.Emph(caption) },
    }, false
  end,

  Table = function(t)
    local caption = pandoc.utils.blocks_to_inlines(t.caption.long)
    if #caption == 0 then return nil end  -- bare tabular: not numbered in LaTeX
    tab = tab + 1
    local n = prefixed(tab)
    local id = t.identifier ~= "" and t.identifier or table_label
    table_label = nil
    caption:insert(1, pandoc.Strong { pandoc.Str("Table " .. n .. ":") })
    caption:insert(2, pandoc.Space())
    t.caption = pandoc.Caption()
    t.identifier = ""
    local out = {}
    if id and id ~= "" then
      numbers[id] = n
      table.insert(out, pandoc.Para { anchor(id) })
    end
    table.insert(out, pandoc.Para { pandoc.Emph(caption) })
    table.insert(out, t)
    return out
  end,

  Div = function(d)
    if d.identifier == "refs" then
      return {
        pandoc.RawBlock("html", "<!-- chapter:  -->"),
        pandoc.Header(1, "Bibliography", { "bibliography", { "unnumbered" } }),
        d,
      }, false
    end
    if d.identifier ~= "" and d.content[1] and d.content[1].t == "Table" then
      -- \begin{table}...\label{tb:x}: pandoc puts the label on a wrapping Div
      table_label = d.identifier
      d.identifier = ""
      return d
    end
    local cls = d.classes[1]
    if cls ~= "Theorem" and cls ~= "Def" then return nil end
    thm[cls] = (thm[cls] or 0) + 1
    local n = chap .. "." .. sec .. "." .. thm[cls]
    if d.identifier ~= "" then numbers[d.identifier] = n end
    local first = d.content[1]
    if first and first.t == "Para" and first.content[1].t == "Strong" then
      local strong = first.content[1].content
      strong[#strong] = pandoc.Str(n)
    end
    -- a plain anchor survives the trip through GFM; the div id does not
    if referenced[d.identifier] then
      table.insert(d.content, 1, pandoc.Plain { anchor(d.identifier) })
    end
    d.identifier = ""
    return d
  end,

  Math = function(m)
    if m.mathtype ~= "DisplayMath" then return nil end
    local text, ids = number_math(m.text)
    m.text = text
    local out = {}
    for _, id in ipairs(ids) do
      if referenced[id] then table.insert(out, anchor(id)) end
    end
    table.insert(out, m)
    return out
  end,
}

-- Pass 3: turn \ref/\eqref links into numbers.
local resolve = {
  -- GFM writes display math as a fenced block, which cannot sit inside
  -- *emphasis* (theorem statements); drop the emphasis around it.
  Emph = function(e)
    local has_display = false
    e:walk { Math = function(m) if m.mathtype == "DisplayMath" then has_display = true end end }
    if has_display then return e.content end
  end,

  Link = function(l)
    local ref = l.attributes["reference"]
    if not ref then return nil end
    local n = numbers[ref]
    if not n then
      io.stderr:write("number.lua: unresolved reference " .. ref .. "\n")
      n = "??"
    end
    if l.attributes["reference-type"] == "eqref" then n = "(" .. n .. ")" end
    l.content = { pandoc.Str(n) }
    l.attributes = {}
    return l
  end,
}

return { collect, number, resolve }
