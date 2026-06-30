line_graph = {
  "HR": { "CR": ["KUR_CR", "CST_CR"], "THR": ["VAD_THR"]},
  "WR": { "THR": ["MAH_THR", "GOR_THR", "RAM_THR", "AND_THR", "BAN_THR"], "CR": ["DAD_CR"], "MLN1":["AND_WR"]},
  "CR": { "HR": ["KUR_HR", "CST_HR"],  "WR": ["DAD_WR"], "MLN1":["GTK_MLN1"]},
  "THR":{ "HR": ["VAD_HR", "CST_HR"], "WR": ["MAH_WR", "GOR_WR", "RAM_WR", "AND_WR","BAN_WR"], "MLN1":["AND_THR"]},
  "MLN1":{ "WR": ["AND_WR"], "THR":["AND_THR"], "CR":["GHA_CR"]},
}