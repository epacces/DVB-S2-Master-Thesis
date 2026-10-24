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

-- Unwrap Emph around figure/table captions so they can be styled.
function Para(p)
  if #p.content == 1 and p.content[1].t == "Emph" then
    local first = p.content[1].content[1]
    if first and first.t == "Strong" then
      local text = pandoc.utils.stringify(first)
      if text:match("^Figure ") or text:match("^Table ") then
        return pandoc.Div(pandoc.Plain(p.content[1].content), { class = "caption" })
      end
    end
  end
end
