-- Pandoc filter used by tools/build_site.py: rewrite links and image paths
-- from the markdown/ layout to the flat _site/ layout.

local function fix(target)
  target = target:gsub("^%.%./", "")
  target = target:gsub("^README%.md", "index.html")
  target = target:gsub("^([%w%-]+)%.md", "%1.html")
  return target
end

function Link(l)
  l.target = fix(l.target)
  return l
end

function Image(img)
  img.src = fix(img.src)
  return img
end

-- Unwrap Emph around figure/table captions so they can be styled, and make
-- "Figure 4.1:" a link to the figure's own anchor.
function Para(p)
  if #p.content == 1 and p.content[1].t == "Emph" then
    local inlines = p.content[1].content
    local first = inlines[1]
    if first and first.t == "Strong" then
      local text = pandoc.utils.stringify(first)
      local kind, num = text:match("^(%a+) ([%w%.]+):$")
      if kind == "Figure" or kind == "Table" then
        inlines[1] = pandoc.Link(first, "#" .. kind:lower() .. "-" .. num, "", { class = "self-link" })
        return pandoc.Div(pandoc.Plain(inlines), { class = "caption" })
      end
    end
  end
end

-- A "#" link after each heading, pointing at its readable anchor
-- (#section-4.3) when it has one.
function Header(h)
  local id = h.identifier
  for _, el in ipairs(h.content) do
    if el.t == "RawInline" then
      local named = el.text:match('^<a id="((%a+)%-[^"]+)"></a>$')
      if named and (named:match("^section%-") or named:match("^chapter%-")) then id = named end
    end
  end
  if id ~= "" then
    h.content:insert(pandoc.Link("#", "#" .. id, "", { class = "heading-link", ["aria-label"] = "Link to this section" }))
  end
  return h
end
