# Satisfactory toolbelt split calculator
#
# Copyright (c) 1992,2025 Joel Yliluoma - https://iki.fi/bisqwit/
#
# With thanks to IceMoonMagic.

import itertools, functools, math, fractions, bisect, sys
from collections import defaultdict

import graphviz

from partition import find_2_or_3_way_partition
from cut3 import find_three_way_cut, split_into_three_groups, split_into_two_groups
from cache import cached

def bisect_range(code, output_value):
  k   = lambda line: line[0]
  left  = bisect.bisect_left(code, output_value, key=k)
  right = bisect.bisect_right(code, output_value, key=k)
  return [p for p in range(left,right) if code[p][2]=='output']

def lines_to_labels(code, pfx, first):
  trans = ["%s_%d" % (pfx,n) for n in range(len(code))]
  if first is not None:
    for n, line in enumerate(code):
      if line[1] == 'input':
       trans[n] = first
       break
  res = []
  for n, line in enumerate(code):
    if line[1] == 'input':
      continue
    res.append( [line[0], trans[n], line[1]] + sorted([trans[c] for c in line[2:]]) )
  return sorted(res)

def labels_to_lines(code, first, total):
  trans = {}
  n = 0
  if first is not None:
    trans[first] = 0
    n += 1
  for line in code:
    r = [1] + list(range(3, len(line)))
    for l in r:
      if line[l] not in trans:
        trans[line[l]] = n
        n += 1
  res = [None] * n
  res[0] = [total, 'input']
  for line in code:
    res[trans[line[1]]] = line[0:1] + line[2:3] + sorted([trans[k] for k in line[3:]])
  #print("TRANS",trans)
  return res

def change_source(lines, old_first, new_first):
  res = []
  for line in lines:
    if line[2] != 'input':
      res.append( line[0:3] + [new_first if q==old_first else q for q in line[3:]] )
  #return lines
  return res

def list_except(list, *indices):
  res = []
  prev = 0
  for i in sorted(indices):
    res += list[prev:i]
    prev = i+1
  res += list[prev:]
  return res

checking = defaultdict(int)
def smartsplit(total, portions):
  global checking
  print("smartsplit(",total,",",portions,")")
  if len(portions) == 0:
    if total == 0:
      yield [[total, 'input'], [total, 'output', 0]]
  elif len(portions) == 1:
    if total == portions[0]:
      yield [[total, 'input'], [total, 'output', 0]]
  else:
    # Is there a way to divide the list into 2 groups that have equal sum?
    # Is there a way to divide the list into 3 groups that have equal sum?
    res = find_2_or_3_way_partition(portions)
    if res is not None:
      k,groups = res
      if k <= len(portions) or True:
        #print("FOUND ",k,"-GROUPING",groups)
        sol  = [[total,'ss','split%d'%k,'s']]
        for gno,g in enumerate(groups):
          l = "g" + str(gno)
          lf = "%s_fst"% l
          p = do_smartsplit(*sorted(g))
          if p is None:
            sol = []
            break
          # Change lines that source "lf" to sourcing "ss" instead
          q = change_source(lines_to_labels(p,l,lf),lf,'ss')
          #print("PARAM:",p, "--", q)
          sol += q
        if len(sol):
          #print("MADE:",sol)
          yield labels_to_lines(sorted(sol), 's', total)
      return

    # Change all portions to same denominator.
    if True:
      frac = [list(fractions.Fraction(v).as_integer_ratio()) for v in portions]
      lcd = math.lcm(*(f[1] for f in frac))
      for f in frac:
          b = lcd // f[1]
          f[0] *= b
          f[1] *= b
      gcf = math.gcd(*(f[0] for f in frac))
      if any(f[0] != gcf for f in frac) and not any(f[1] != 1 for f in frac):
        test   = []
        merges = []
        foil = False
        for f in frac:
          num = gcf if f[1] == 1 else (gcf / f[1])
          test += [num] * (f[0] // gcf)
          if f[0] != gcf:# and num != 1:
            times = f[0]//gcf
            if times > 10:
              foil = True
              break
            merges.append((f[0]/f[1], num/f[1], times)) # orig,piece,times

        if len(merges) and not foil:
          res = do_smartsplit(*sorted(test))
          if res:
            spl = lines_to_labels(res, 'p', 's')
            print("SOLUTION FOR ",test," FROM ",portions,": ",spl)
            combsets = []
            for orig,piece,times in merges:
              # Find all instances of line with 'output' with "piece" value.
              # Pick "times" of those, and delete those and add a 'merge' line with those labels as params.
              found = [spl[pos][1] for pos in bisect_range(spl, piece)]
              #combs = [list(q) for q in itertools.combinations(found, times)]
              combs = []
              for q in itertools.combinations(found, times):
                combs.append(q)
                break
              #print("COMBS:",combs)
              combsets.append(combs)
            #print("MERGE ",merges," PROPOSALS:", combsets)
            # Change the code into a dict
            spl = {line[1]:line for line in spl}
            # Perform the merges
            for sels in itertools.product(*combsets):
              #print("SELS:",sels)
              # Make sure no two "sels" refers to same elements
              if len(set(q for z in sels for q in z)) != sum(len(z) for z in sels):
                continue
              # Make a copy of the dict
              wip = {k:spl[k] for k in spl}
              for sno,(orig,piece,times) in enumerate(merges):
                #print("sels[%d]=%s" % (sno,sels[sno]))
                wip["merge%d"%sno] = [orig,"merge%d"%sno, 'merge'] + [wip[q][3] for q in sels[sno]]
                wip["out%d"%sno]   = [orig,"out%d"%sno,   'output',"merge%d"%sno]
                for in_label in sels[sno]:
                  del wip[in_label]
              # Change the dict back into a list
              #print("MERGED PROPOSAL:",list(wip.values()))#,labels_to_lines(wip.values(), 's', total))
              yield labels_to_lines(wip.values(), 's', total)
    
    if (total%6 != 0) and total >= 2:
      for div in (3,2,6):
        if total%div != 0:
          miss = div - total%div
          p    = sorted(list(portions) + [miss])
          q = tuple(p)
          if checking[q]:
            continue
          checking[q] += 1
          res = do_smartsplit(*p)
          checking[q] -= 1
          if res:
            spl = lines_to_labels(res, 'p', 's')
            # Find the an instance of line with 'output' with "miss" value.
            # Delete that line, and add a 'merge' line with that label and the top label of what we received.
            #print("Find ",miss,":", bisect_range(spl,miss)," in ",spl)
            for pos in bisect_range(spl, miss):
              cand = spl[:pos] + spl[pos+1:] + [[total+miss, 's', 'merge', 'k', spl[pos][3]]]
              #print("FROM",total+miss, spl)
              #print("CAND",total,      cand)
              out = labels_to_lines(cand, 'k', total)
              #print("OUT ", out)
              yield out
    
    def twoway_split(left,right, sum, left_extra,right_extra):
      leftpos  = bisect_range(left, left_extra)
      rightpos = bisect_range(right, right_extra)
      base   = [[total, 'ss','split2','s'],
                [sum,   'eo','output','extra']]
      for li in leftpos:
        for ri in rightpos:
          combined = (base +
                      [[sum, 'extra', 'merge', left[li][3], right[ri][3]]] +
                      list_except(left, li) +
                      list_except(right, ri))
          temp = labels_to_lines(combined, 's', total)
          yield temp

    if (total % 2 == 0 or total >= 2) and len(portions) <= 8:
      #for i,value in enumerate(portions):
      half = total//2
      done_tests = set()
      for perm in itertools.permutations(portions):
        perm = list(perm)
        ret = split_into_two_groups(perm)
        if ret is None: continue
        i,alpha,common_sum = ret
        group1 = sorted(perm[:i]   + [left_extra  := round(alpha*perm[i], 5)])
        group2 = sorted(perm[i+1:] + [right_extra := round((1-alpha)*perm[i], 5)])
        t = tuple(group1)
        if t in done_tests: continue
        done_tests.add(t)
        left = do_smartsplit(*group1)
        if not left: continue
        right = do_smartsplit(*group2)
        if not right: continue
        left  = lines_to_labels(left,  'p', 'ss')
        right = lines_to_labels(right, 'q', 'ss')
        yield from twoway_split(left,right, perm[i], left_extra,right_extra)
    
    if (total % 3 == 0 or total >= 3) and len(portions) <= 8 and False:
      done_tests = set()
      for perm in itertools.permutations(portions):
        perm = list(perm)
        ret = split_into_three_groups(perm)
        if ret is None: continue
        i,alpha,j,beta,common_sum = ret
        group1 = sorted(perm[:i]    + [left_extra := round(alpha*perm[i], 5)])
        group2 = sorted(perm[i+1:j] + [mid_extra1 := round((1-alpha)*perm[i], 5)] + [mid_extra2 := round(beta*perm[j], 5)])
        group3 = sorted(perm[j+1:]  + [right_extra:= round((1-beta)*perm[j], 5)])
        t = (tuple(group1), tuple(group2))
        if t in done_tests: continue
        done_tests.add(t)
        part1 = do_smartsplit(*group1)
        if not part1: continue
        part2 = do_smartsplit(*group2)
        if not part2: continue
        part3 = do_smartsplit(*group3)
        if not part3: continue
        left  = lines_to_labels(part1, 'p', 'ss')
        mid   = lines_to_labels(part2, 'q', 'ss')
        right = lines_to_labels(part3, 'r', 'ss')
        leftpos  = bisect_range(left, left_extra)
        midpos1  = bisect_range(mid,  mid_extra1)
        midpos2  = bisect_range(mid,  mid_extra2)
        rightpos = bisect_range(right, right_extra)
        
        if not len(midpos1) or not len(leftpos):
          yield from twoway_split(left+mid, right, perm[j], mid_extra2,right_extra)
        elif not len(rightpos) or not len(midpos2):
          yield from twoway_split(left, mid+right, perm[i], left_extra,mid_extra1)
        else:
          base   = [[total,     'ss','split3','s'],
                    [perm[i],  'eo1','output','extra1'],
                    [perm[j],  'eo2','output','extra2']]
          for mi1 in midpos1:
           for mi2 in midpos2:
            if mi1 < mi2:
             for li in leftpos:
              for ri in rightpos:
                combined = (base +
                            [[perm[i], 'extra1', 'merge', left[li][3], mid[mi1][3]],
                             [perm[j], 'extra2', 'merge', mid[mi2][3], right[ri][3]],
                            ] +
                            list_except(left, li) +
                            list_except(mid, mi1, mi2) +
                            list_except(right, ri))
                print("COMBINED", combined)
                temp = labels_to_lines(combined, 's', total)
                print("BECAME", temp)
                yield temp

def eval_cost(option):
  return len(option) #sum(q[1] not in ('input','output') for q in option)

def validate(choices, code):
  found = [code[i][0] for i in range(len(code)) if code[i][1]=='output']
  if sorted(found) != sorted(choices):
    print("CODE DOES NOT SATISFY ",choices," -- GOT ",found)
    for i,opt in enumerate(code):
      print("  %3d: %s" % (i, opt))
    
def cleanup(total, code):
  # If a merge pulls the same 'split2' twice, replace both sources with the split's source
  # If a merge pulls the same 'split3' thrice, replace the three sources with the split's source
  # If a merge has only one source, replace all pulls from this merge with pulls from the merge's source and delete the merge line
  # If a merge pulls from a merge, merge the merges and reroute sources
  spl = lines_to_labels(code, 'p', 's')
  spl = {line[1]:line for line in spl}
  #print("Before clean:", spl)

  is_split = {k:[spl[k][3],0] for k in spl if spl[k][2][:5]=='split'}
  # For each split, determing how their k by counting how many nodes refer to it
  for k in spl:
    for q in spl[k][3:]:
      if q in is_split:
        is_split[q][1] += 1
  redo = True
  while redo:
    redo = False
    is_merge = set(k for k in spl if spl[k][2] == 'merge')
    for k in is_merge:
      uses = defaultdict(int)
      for s in spl[k][3:]:
        uses[s] += 1
      changes = True
      redo    = False
      while changes:
        changes = False
        for s in uses:
          if s in is_merge and uses[s] > 0:
            # Add the referenced merge's sources
            for s2 in spl[s][3:]:
              uses[s2] += uses[s]
            # And stop referring to that merge
            uses[s] = 0
            changes = True
            break
          if s in is_split and uses[s] >= is_split[s][1]:
            uses[is_split[s][0]] += uses[s] // is_split[s][1]
            uses[s]            %= is_split[s][1]
            changes = True
            break
        if changes:
          redo = True
      if sum(uses.values()) == 1:
        redo = True
        for s in uses:
          pass
        # Replace all uses of k with s
        for q in spl:
          for i in range(3, len(spl[q])):
            if spl[q][i] == k:
              spl[q][i] = s
        del spl[k]
      elif redo:
        r = []
        for s in uses:
          r += [s] * uses[s]
        spl[k] = spl[k][:3] + r
  #print("After  clean:", spl)
  # Finally do a DFS through the tree and delete inaccessible nodes
  if True: # BFS
    todo    = [k for k in spl if spl[k][2] == 'output']
    visited = set()
    for k in todo:
      if k not in visited:
        visited.add(k)
        for q in spl[k][3:]:
          if q not in visited and q != 's':
            todo.append(q)
  else: # DFS
    visited = set()
    def dfs(k):
      if k != 's' and k not in visited:
        visited.add(k)
        for q in spl[k][3:]:
          dfs(q)
    for k in spl:
      if spl[k][2] == 'output':
        dfs(k)
  return labels_to_lines([spl[k] for k in visited], 's', total)


#from joblib import Memory
#memory = Memory("cachedir")
#@memory.cache
@cached
def do_smartsplit(*nums):
  res = None
  nums = [q for q in nums if q]
  for option in smartsplit(sum(nums), nums):
    if option is None:
      continue
    validate(nums, option)
    option = cleanup(sum(nums), option)
    cost = eval_cost(option)
    if res is None or cost < res[0]:
      res = [cost, option]
  return res[1] if res else None

if len(sys.argv) == 1:
  print("Usage: python3 smartsplit.py <output> [<...>]")
  sys.exit()

view_graph = True

opt = do_smartsplit(*(float(v) for v in sys.argv[1:]))
if opt:
  for i,line in enumerate(opt):
    print("%3d: %s" % (i, line))

  feeders = defaultdict(int)
  for i,line in enumerate(opt):
    for q in line[2:]:
      feeders[q] += 1

  shapes = {
   'input':'house style=filled fillcolor=lightblue',
   'output':'invhouse style=filled fillcolor=lightgreen',
   'merge':'square',
   'split':'diamond','split2':'diamond','split3':'diamond'
  }
  dot = "graph [splines=spline]\n"
  dot += "{rank=max;"
  for i,line in enumerate(opt):
    if opt[i][1] == 'output':
      dot += "node%d;" % i
  dot += "}"

  dot += "{rank=min;"
  for i,line in enumerate(opt):
    if opt[i][1] == 'input':
      dot += "node%d;" % i
  dot += "}"
  
  for i,line in enumerate(opt):
    label = '%g' % line[0]
    if line[1] == 'merge':
      label = '%s=%s' % ('+'.join('%g'%v for v in sorted(((opt[q][0]/feeders[q]) for q in line[2:]), reverse=True)), label)
    elif line[1][:5] == 'split':
      label = '%s /%d' % (label, feeders[i])
    
    dot += "node%d [label=\"%s\" shape=%s]\n" % (i, label, shapes[line[1]])
    for q in line[2:]:
      flow = opt[q][0] / (feeders[q] if feeders[q] else 1)
      dot += "node%d->node%d [label=\"%g\"];\n" % (q, i, flow)

  if view_graph:
    graph = graphviz.Digraph(body=dot)
    graph.view()
  else:
    print("digraph {\n%s}" % dot)
else:
  print("No solution")

cached.save()
