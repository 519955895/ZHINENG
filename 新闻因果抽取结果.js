window.NEWS_DATA_STAMP = '9f52defc63';
window.NEWS_DATA = [
  {
    "news_id": "news_001",
    "url": "",
    "title": "",
    "category": "事故",
    "category_evidence": [
      "交通事故",
      "越过绿化带碰撞",
      "造成1人死亡、2人受伤",
      "刑事拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "杨某某驾车越过绿化带，碰撞停在非机动车道上的一辆二轮电动车",
        "original_text": "越过绿化带碰撞停在非机动车道上的一辆二轮电动车，",
        "entities": [
          {
            "name": "20260620",
            "type": "时间",
            "role": "事故发生时间"
          },
          {
            "name": "安徽省广德市太极大道",
            "type": "地点",
            "role": "事故发生地点"
          },
          {
            "name": "杨某某（女，36岁）",
            "type": "人物",
            "role": "肇事驾驶人"
          },
          {
            "name": "二轮电动车",
            "type": "其他",
            "role": "被碰撞车辆"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "事故造成1人死亡、2人受伤，其中1人伤势较重",
        "original_text": "造成1人死亡、2人受伤（1人伤势较重）。",
        "entities": [],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关接警到场处置，并联动120急救部门救治伤员",
        "original_text": "接警后，公安机关迅速组织警力到场处置并联动120急救部门开展伤员救治工作。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "现场处置机构"
          },
          {
            "name": "120急救部门",
            "type": "机构",
            "role": "伤员救治机构"
          }
        ],
        "event_type": [
          "事故",
          "社会"
        ]
      },
      {
        "event_id": "E4",
        "description": "杨某某因涉嫌犯罪当晚被公安机关依法刑事拘留",
        "original_text": "当晚，杨某某已被公安机关依法刑事拘留。",
        "entities": [
          {
            "name": "杨某某（女，36岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          },
          {
            "name": "公安机关",
            "type": "机构",
            "role": "刑事拘留决定机关"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "经调查，杨某某（女，36岁）驾驶一辆小型普通客车沿太极大道由东向西行驶时，越过绿化带碰撞停在非机动车道上的一辆二轮电动车，造成1人死亡、2人受伤（1人伤势较重）。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "通报称，6月20日15时36分许，广德市发生一起交通事故。接警后，公安机关迅速组织警力到场处置并联动120急救部门开展伤员救治工作。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C3",
        "cause_event_id": "E1",
        "effect_event_id": "E4",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经调查，杨某某（女，36岁）驾驶一辆小型普通客车沿太极大道由东向西行驶时，越过绿化带碰撞停在非机动车道上的一辆二轮电动车，造成1人死亡、2人受伤（1人伤势较重）。当晚，杨某某已被公安机关依法刑事拘留。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "驾车碰撞事故 → 1死2伤"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "驾车碰撞事故 → 公安处置与伤员救治"
      },
      {
        "chain_id": "C3",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "驾车碰撞事故 → 肇事者被刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_002",
    "url": "",
    "title": "",
    "category": "事故",
    "category_evidence": [
      "道路交通事故",
      "与行人发生碰撞",
      "造成1人死亡，11人不同程度受伤",
      "逃逸"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "李某某驾车右转时与行人发生碰撞",
        "original_text": "经初步调查，李某某（男，31岁）驾驶一辆小型轿车行驶至剑南大道与天府四街交叉路口右转时，与行人发生碰撞。",
        "entities": [
          {
            "name": "20260501",
            "type": "时间",
            "role": "事故发生时间"
          },
          {
            "name": "高新区剑南大道与天府四街交叉路口",
            "type": "地点",
            "role": "事故发生地点"
          },
          {
            "name": "李某某（男，31岁）",
            "type": "人物",
            "role": "肇事驾驶人"
          },
          {
            "name": "小型轿车",
            "type": "其他",
            "role": "肇事车辆"
          },
          {
            "name": "行人（未具名）",
            "type": "人物",
            "role": "被碰撞者"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "李某某驾车逃离现场，逃逸过程中又与多辆车辆及行人碰撞",
        "original_text": "随后，李某某驾车逃离现场，在逃逸过程中又先后与其他车辆及行人发生碰撞。",
        "entities": [
          {
            "name": "李某某（男，31岁）",
            "type": "人物",
            "role": "肇事逃逸人"
          }
        ],
        "event_type": [
          "事故",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "事故共造成1人死亡、11人不同程度受伤，伤者均已送医",
        "original_text": "事故共造成1人死亡，11人不同程度受伤。目前所有伤者均已送医治疗。",
        "entities": [],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E4",
        "description": "公安机关接警到场处置，并联动120急救部门救治伤员",
        "original_text": "接报警后，公安机关迅速组织警力到场处置，并联动120急救部门开展伤员救治工作。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "现场处置机构"
          },
          {
            "name": "120急救部门",
            "type": "机构",
            "role": "伤员救治机构"
          }
        ],
        "event_type": [
          "事故",
          "社会"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "经初步调查，李某某（男，31岁）驾驶一辆小型轿车行驶至剑南大道与天府四街交叉路口右转时，与行人发生碰撞。随后，李某某驾车逃离现场，在逃逸过程中又先后与其他车辆及行人发生碰撞。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.8,
        "evidence_text": "随后，李某某驾车逃离现场，在逃逸过程中又先后与其他车辆及行人发生碰撞。事故共造成1人死亡，11人不同程度受伤。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E4",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "2026年5月1日17时20分许，我市高新区剑南大道发生一起道路交通事故。接报警后，公安机关迅速组织警力到场处置，并联动120急救部门开展伤员救治工作。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "碰撞后逃逸再碰撞 → 1死11伤"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "交通事故 → 公安处置与伤员救治"
      }
    ]
  },
  {
    "news_id": "news_003",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "发生口角",
      "引发肢体冲突",
      "行政拘留处罚",
      "行政罚款处罚"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "卢某因蒙某等一行人聊天声音问题在航班上与其发生口角",
        "original_text": "乘客卢某（男，34岁）因乘客蒙某（女，38岁）、张某（女，37岁）、白某某（男，38岁）、雷某某（男，39岁）一行人聊天声音的问题发生口角，",
        "entities": [
          {
            "name": "民航航班（飞行途中）",
            "type": "地点",
            "role": "事发地点"
          },
          {
            "name": "卢某（男，34岁）",
            "type": "人物",
            "role": "口角一方"
          },
          {
            "name": "蒙某（女，38岁）",
            "type": "人物",
            "role": "同行乘客，聊天声音被指一方"
          },
          {
            "name": "张某（女，37岁）",
            "type": "人物",
            "role": "同行乘客，聊天声音被指一方"
          },
          {
            "name": "白某某（男，38岁）",
            "type": "人物",
            "role": "同行乘客，聊天声音被指一方"
          },
          {
            "name": "雷某某（男，39岁）",
            "type": "人物",
            "role": "同行乘客，聊天声音被指一方"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E2",
        "description": "口角引发肢体冲突，卢某、蒙某身体被不同程度抓伤",
        "original_text": "进而引发肢体冲突，卢某、蒙某身体被不同程度抓伤。",
        "entities": [
          {
            "name": "卢某（男，34岁）",
            "type": "人物",
            "role": "冲突参与者、受伤者"
          },
          {
            "name": "蒙某（女，38岁）",
            "type": "人物",
            "role": "冲突参与者、受伤者"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "机场公安局对卢某、蒙某、张某行政拘留，对白某某、雷某某行政罚款",
        "original_text": "目前，机场公安局已依法对卢某、蒙某、张某作出行政拘留处罚，对白某某、雷某某作出行政罚款处罚。",
        "entities": [
          {
            "name": "机场公安局",
            "type": "机构",
            "role": "处罚机关"
          },
          {
            "name": "卢某、蒙某、张某",
            "type": "人物",
            "role": "被行政拘留处罚人"
          },
          {
            "name": "白某某、雷某某",
            "type": "人物",
            "role": "被行政罚款处罚人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "经查，航班飞行过程中，乘客卢某（男，34岁）因乘客蒙某（女，38岁）、张某（女，37岁）、白某某（男，38岁）、雷某某（男，39岁）一行人聊天声音的问题发生口角，进而引发肢体冲突，卢某、蒙某身体被不同程度抓伤。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经查，航班飞行过程中，乘客卢某（男，34岁）因乘客蒙某（女，38岁）、张某（女，37岁）、白某某（男，38岁）、雷某某（男，39岁）一行人聊天声音的问题发生口角，进而引发肢体冲突，卢某、蒙某身体被不同程度抓伤。目前，机场公安局已依法对卢某、蒙某、张某作出行政拘留处罚，对白某某、雷某某作出行政罚款处罚。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "口角 → 肢体冲突致伤 → 机场公安局处罚"
      }
    ]
  },
  {
    "news_id": "news_004",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "警情通报",
      "涉嫌猥亵儿童罪",
      "刑事拘留",
      "女性未成年人"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "郑某某在海口挑选演员期间以指导舞蹈动作为由猥亵参加排练的女性未成年人",
        "original_text": "经查，犯罪嫌疑人郑某某在海口挑选演员期间，以指导舞蹈动作为由，对参加排练的女性未成年人进行猥亵。",
        "entities": [
          {
            "name": "海口",
            "type": "地点",
            "role": "案发地点"
          },
          {
            "name": "郑某某（男，58岁）",
            "type": "人物",
            "role": "犯罪嫌疑人"
          },
          {
            "name": "女性未成年人（未具名）",
            "type": "人物",
            "role": "受害人"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "警方接报警后开展工作，于1月17日将郑某某抓获",
        "original_text": "接报警后，警方迅速开展工作，于1月17日将郑某某抓获。",
        "entities": [
          {
            "name": "20260117",
            "type": "时间",
            "role": "抓获时间"
          },
          {
            "name": "海口市公安局龙华分局",
            "type": "机构",
            "role": "侦办机关"
          },
          {
            "name": "郑某某（男，58岁）",
            "type": "人物",
            "role": "被抓获人"
          }
        ],
        "event_type": [
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "郑某某因涉嫌猥亵儿童罪被海口市公安局龙华分局刑事拘留",
        "original_text": "人民网海口2月19日电 （记者孟凡盛）2月19日晚，海南省海口市公安局龙华分局发布警情通报称，1月18日，郑某某（男，58岁）因涉嫌猥亵儿童罪被海口市公安局龙华分局刑事拘留。",
        "entities": [
          {
            "name": "20260118",
            "type": "时间",
            "role": "刑事拘留时间"
          },
          {
            "name": "郑某某（男，58岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经查，犯罪嫌疑人郑某某在海口挑选演员期间，以指导舞蹈动作为由，对参加排练的女性未成年人进行猥亵。接报警后，警方迅速开展工作，于1月17日将郑某某抓获。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "人民网海口2月19日电（记者孟凡盛）2月19日晚，海南省海口市公安局龙华分局发布警情通报称，1月18日，郑某某（男，58岁）因涉嫌猥亵儿童罪被海口市公安局龙华分局刑事拘留。经查，犯罪嫌疑人郑某某在海口挑选演员期间，以指导舞蹈动作为由，对参加排练的女性未成年人进行猥亵。接报警后，警方迅速开展工作，于1月17日将郑某某抓获。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "猥亵未成年人 → 警方抓获 → 刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_005",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "警情通报",
      "辱骂",
      "立案",
      "违法行为人"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "男子搭讪被拒后当众指责并持续辱骂女游客",
        "original_text": "视频中，一名女游客在青岛海之恋公园独自拍照时，一名男子上前搭讪询问相机品牌、价格，被婉拒后，大声指责女游客“违规占道影响跑步”。即便女游客道歉，仍持续辱骂女游客。",
        "entities": [
          {
            "name": "青岛海之恋公园",
            "type": "地点",
            "role": "发生地点"
          },
          {
            "name": "男游客（未具名）",
            "type": "人物",
            "role": "辱骂者"
          },
          {
            "name": "女游客（未具名）",
            "type": "人物",
            "role": "受害人"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "崂山公安分局立案调查，违法行为人到案",
        "original_text": "8月20日，崂山公安分局发布警情通报称，已立案开展全面调查，违法行为人已到案。",
        "entities": [
          {
            "name": "20250820",
            "type": "时间",
            "role": "立案时间"
          },
          {
            "name": "崂山公安分局",
            "type": "机构",
            "role": "处置机构"
          }
        ],
        "event_type": [
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关将根据调查情况依法处理并公布结果",
        "original_text": "下一步，将根据调查取证情况依法处理，并及时向社会公布。",
        "entities": [],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "即便女游客道歉，仍持续辱骂女游客。8月20日，崂山公安分局发布警情通报称，已立案开展全面调查，违法行为人已到案。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "8月20日，崂山公安分局发布警情通报称，已立案开展全面调查，违法行为人已到案。下一步，将根据调查取证情况依法处理，并及时向社会公布。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "辱骂行为 → 公安立案调查 → 后续依法处理"
      }
    ]
  },
  {
    "news_id": "news_006",
    "url": "",
    "title": "",
    "category": "事故",
    "category_evidence": [
      "碰撞事故",
      "导致4人死亡，2人受伤"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "重型半挂牵引车与小型普通客车在武宣县省道路段发生碰撞事故",
        "original_text": "发生一起重型半挂牵引车与小型普通客车碰撞事故，",
        "entities": [
          {
            "name": "20260630",
            "type": "时间",
            "role": "事故发生时间"
          },
          {
            "name": "广西来宾市武宣县省道S304线232公里700米处",
            "type": "地点",
            "role": "事故发生地点"
          },
          {
            "name": "重型半挂牵引车",
            "type": "其他",
            "role": "肇事车辆"
          },
          {
            "name": "小型普通客车",
            "type": "其他",
            "role": "被碰撞车辆"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "事故导致4人死亡、2人受伤",
        "original_text": "导致4人死亡，2人受伤。",
        "entities": [],
        "event_type": [
          "事故"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.97,
        "evidence_text": "2026年6月30日15时许，在来宾市武宣县省道S304线232公里700米处路段，发生一起重型半挂牵引车与小型普通客车碰撞事故，导致4人死亡，2人受伤。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "车辆碰撞事故 → 4死2伤"
      }
    ]
  },
  {
    "news_id": "news_007",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "治安案件",
      "口角",
      "肢体冲突",
      "依法立案"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "苏某、徐某就餐时与邻桌宋某因口角先后发生肢体冲突",
        "original_text": "经查，6月12日12时许，苏某（男，49岁）、徐某（女，36岁）就餐时与邻桌宋某（女，15岁）因口角先后发生肢体冲突。案件事实由现场视频监控、当事人陈述、证人证言等证据证实。",
        "entities": [
          {
            "name": "20260612",
            "type": "时间",
            "role": "案发时间"
          },
          {
            "name": "某快餐店",
            "type": "地点",
            "role": "事发地点"
          },
          {
            "name": "苏某（男，49岁）",
            "type": "人物",
            "role": "冲突一方"
          },
          {
            "name": "徐某（女，36岁）",
            "type": "人物",
            "role": "冲突一方"
          },
          {
            "name": "宋某（女，15岁）",
            "type": "人物",
            "role": "冲突另一方"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E2",
        "description": "公安机关接警介入处置，依法立案并开展走访调查、证据固定及伤情鉴定",
        "original_text": "6月12日，我区某快餐店内发生一起治安案件，公安机关接警后迅速介入处置，依法立案并开展走访调查、证据固定及伤情鉴定等工作。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "处置机关"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "6月12日，我区某快餐店内发生一起治安案件，公安机关接警后迅速介入处置，依法立案并开展走访调查、证据固定及伤情鉴定等工作。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "快餐店冲突 → 公安立案调查"
      }
    ]
  },
  {
    "news_id": "news_008",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "焚烧耕地秸秆",
      "引燃邻近田地",
      "造成他人财产损失",
      "行政拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "刘某某、余某某焚烧耕地秸秆，引燃邻近田地",
        "original_text": "襄州区朱集镇下湾村村民刘某某、黄集镇大王村村民余某某，焚烧耕地秸秆",
        "entities": [
          {
            "name": "日期不详",
            "type": "时间",
            "role": "焚烧发生时间（近日）"
          },
          {
            "name": "刘某某",
            "type": "人物",
            "role": "焚烧秸秆者"
          },
          {
            "name": "余某某",
            "type": "人物",
            "role": "焚烧秸秆者"
          },
          {
            "name": "襄州区朱集镇下湾村",
            "type": "地点",
            "role": "刘某某焚烧秸秆地点"
          },
          {
            "name": "襄州区黄集镇大王村",
            "type": "地点",
            "role": "余某某焚烧秸秆地点"
          }
        ],
        "event_type": [
          "社会",
          "环境"
        ]
      },
      {
        "event_id": "E2",
        "description": "火势引燃邻近田地，造成他人财产损失",
        "original_text": "引燃邻近田地，造成他人财产损失。",
        "entities": [
          {
            "name": "他人（未具名）",
            "type": "人物",
            "role": "财产受损者"
          },
          {
            "name": "邻近田地",
            "type": "地点",
            "role": "过火地点"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关依法对刘某某、余某某行政拘留",
        "original_text": "目前，刘某某、余某某已被公安机关依法行政拘留。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "处罚机关"
          },
          {
            "name": "刘某某",
            "type": "人物",
            "role": "被行政拘留人"
          },
          {
            "name": "余某某",
            "type": "人物",
            "role": "被行政拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "近日，襄州区朱集镇下湾村村民刘某某、黄集镇大王村村民余某某，焚烧耕地秸秆引燃邻近田地，造成他人财产损失。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "近日，襄州区朱集镇下湾村村民刘某某、黄集镇大王村村民余某某，焚烧耕地秸秆引燃邻近田地，造成他人财产损失。目前，刘某某、余某某已被公安机关依法行政拘留。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "焚烧秸秆引燃田地 → 他人财产损失"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "焚烧秸秆违法行为 → 行政拘留"
      }
    ]
  },
  {
    "news_id": "news_009",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "虚假“警情通报”",
      "谣言传播扩散",
      "扰乱公共秩序",
      "刑事拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "白某某、陈某某为博取关注在互联网平台传播虚假警情通报",
        "original_text": "白某某（男，29岁）、陈某某（男，18岁）2人为博取关注、吸引眼球，通过互联网平台传播虚假“警情通报”，",
        "entities": [
          {
            "name": "白某某（男，29岁）",
            "type": "人物",
            "role": "造谣传谣者"
          },
          {
            "name": "陈某某（男，18岁）",
            "type": "人物",
            "role": "造谣传谣者"
          },
          {
            "name": "互联网平台",
            "type": "其他",
            "role": "传播渠道"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "谣言传播扩散，扰乱公共秩序",
        "original_text": "造成谣言传播扩散，扰乱公共秩序。",
        "entities": [],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关依法对白某某、陈某某刑事拘留",
        "original_text": "目前，公安机关已依法对白某某、陈某某刑事拘留。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "处罚机关"
          },
          {
            "name": "白某某（男，29岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          },
          {
            "name": "陈某某（男，18岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "经查，白某某（男，29岁）、陈某某（男，18岁）2人为博取关注、吸引眼球，通过互联网平台传播虚假“警情通报”，造成谣言传播扩散，扰乱公共秩序。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经查，白某某（男，29岁）、陈某某（男，18岁）2人为博取关注、吸引眼球，通过互联网平台传播虚假“警情通报”，造成谣言传播扩散，扰乱公共秩序。目前，公安机关已依法对白某某、陈某某刑事拘留。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "传播虚假警情通报 → 谣言扩散扰乱公共秩序"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "传播虚假警情通报 → 刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_010",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "虚假“警情通报”",
      "谣言传播扩散",
      "扰乱公共秩序",
      "刑事拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "黄某忠为博取关注在互联网平台发布虚假警情通报",
        "original_text": "黄某忠（男、39岁）为博取关注、吸引眼球，在互联网平台发布该虚假“警情通报”，",
        "entities": [
          {
            "name": "黄某忠（男，39岁）",
            "type": "人物",
            "role": "造谣者"
          },
          {
            "name": "互联网平台",
            "type": "其他",
            "role": "发布渠道"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "谣言传播扩散，扰乱公共秩序",
        "original_text": "造成谣言传播扩散，扰乱公共秩序。",
        "entities": [],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关依法对黄某忠刑事拘留",
        "original_text": "目前，公安机关已依法对黄某忠刑事拘留。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "处罚机关"
          },
          {
            "name": "黄某忠（男，39岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "经查，黄某忠（男、39岁）为博取关注、吸引眼球，在互联网平台发布该虚假“警情通报”，造成谣言传播扩散，扰乱公共秩序。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经查，黄某忠（男、39岁）为博取关注、吸引眼球，在互联网平台发布该虚假“警情通报”，造成谣言传播扩散，扰乱公共秩序。目前，公安机关已依法对黄某忠刑事拘留。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "发布虚假警情通报 → 谣言扩散扰乱公共秩序"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "发布虚假警情通报 → 刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_011",
    "url": "",
    "title": "",
    "category": "事故",
    "category_evidence": [
      "正在装修的餐厅发生火灾",
      "造成6人死亡，3人受伤",
      "明火扑灭"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "海口市正在装修的椰香源餐厅发生火灾",
        "original_text": "通报称，9月3日14时45分，海口市消防救援局指挥中心接到报警，位于海口市秀英大道东侧的正在装修的椰香源餐厅发生火灾。",
        "entities": [
          {
            "name": "20260903",
            "type": "时间",
            "role": "起火时间"
          },
          {
            "name": "海口市秀英大道东侧椰香源餐厅（装修中）",
            "type": "地点",
            "role": "起火地点"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "市消防救援局调集力量赶赴现场扑救，15时23分明火扑灭",
        "original_text": "市消防救援局第一时间调集力量赶赴现场处置，15时23分明火扑灭。",
        "entities": [
          {
            "name": "海口市消防救援局",
            "type": "机构",
            "role": "灭火救援机构"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E3",
        "description": "火灾造成6人死亡、3人受伤，伤者生命体征平稳",
        "original_text": "火灾造成6人死亡，3人受伤(伤者目前生命体征平稳)。",
        "entities": [],
        "event_type": [
          "事故"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "通报称，9月3日14时45分，海口市消防救援局指挥中心接到报警，位于海口市秀英大道东侧的正在装修的椰香源餐厅发生火灾。市消防救援局第一时间调集力量赶赴现场处置，15时23分明火扑灭。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "中新网海口9月3日电 (记者 王子谦)海口市消防救援局3日下午发布警情通报，当日下午该市一家正在装修的餐厅发生火灾，造成6人死亡，3人受伤。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "餐厅火灾 → 消防扑救"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "餐厅火灾 → 6死3伤"
      }
    ]
  },
  {
    "news_id": "news_012",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "殴打、撕扯衣服",
      "引发围观",
      "送伤者就医",
      "刑事拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "霍某某、张某某在公共场所对刘某实施殴打、撕扯衣服，引发围观",
        "original_text": "8月29日中午，霍某某(女，52岁)、张某某(女，53岁)在公共场所对刘某(女，37岁)实施殴打、撕扯衣服行为，引发围观。",
        "entities": [
          {
            "name": "20260829",
            "type": "时间",
            "role": "案发时间"
          },
          {
            "name": "公共场所",
            "type": "地点",
            "role": "案发地点"
          },
          {
            "name": "霍某某（女，52岁）",
            "type": "人物",
            "role": "施暴者"
          },
          {
            "name": "张某某（女，53岁）",
            "type": "人物",
            "role": "施暴者"
          },
          {
            "name": "刘某（女，37岁）",
            "type": "人物",
            "role": "受害人"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E2",
        "description": "民警接警到场处置，送伤者就医并将两名涉案人员控制带回调查",
        "original_text": "接警后，我局民警立即到场处置，送伤者就医治疗，将两名涉案人员控制并带回公安机关调查。",
        "entities": [
          {
            "name": "公安机关",
            "type": "机构",
            "role": "处置机关"
          },
          {
            "name": "霍某某（女，52岁）",
            "type": "人物",
            "role": "被控制调查的涉案人员"
          },
          {
            "name": "张某某（女，53岁）",
            "type": "人物",
            "role": "被控制调查的涉案人员"
          }
        ],
        "event_type": [
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "霍某某、张某某被依法刑事拘留",
        "original_text": "8月30日，霍某某、张某某被依法刑事拘留，目前，案件正在进一步侦办中。",
        "entities": [
          {
            "name": "20260830",
            "type": "时间",
            "role": "刑事拘留时间"
          },
          {
            "name": "霍某某（女，52岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          },
          {
            "name": "张某某（女，53岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "8月29日中午，霍某某(女，52岁)、张某某(女，53岁)在公共场所对刘某(女，37岁)实施殴打、撕扯衣服行为，引发围观。接警后，我局民警立即到场处置，送伤者就医治疗，将两名涉案人员控制并带回公安机关调查。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "接警后，我局民警立即到场处置，送伤者就医治疗，将两名涉案人员控制并带回公安机关调查。8月30日，霍某某、张某某被依法刑事拘留，目前，案件正在进一步侦办中。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "殴打撕扯 → 警方控制调查 → 刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_013",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "警情通报",
      "故意伤害案",
      "致1人受伤"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "玉林市玉州区人民东路一经营门店内发生一起故意伤害案",
        "original_text": "当日15时许，玉林市玉州区人民东路一经营门店内发生一起故意伤害案",
        "entities": [
          {
            "name": "20260901",
            "type": "时间",
            "role": "案发时间"
          },
          {
            "name": "广西玉林市玉州区人民东路一经营门店",
            "type": "地点",
            "role": "案发地点"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "故意伤害案致1人受伤",
        "original_text": "致1人受伤。",
        "entities": [],
        "event_type": [
          "社会",
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "中新网玉林9月2日电(记者 黄艳梅)广西玉林市公安局玉州分局9月1日晚发布警情通报称，当日15时许，玉林市玉州区人民东路一经营门店内发生一起故意伤害案，致1人受伤。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "故意伤害案 → 1人受伤"
      }
    ]
  },
  {
    "news_id": "news_014",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "意外摔倒",
      "交涉",
      "抓咬、撕扯",
      "轻微伤",
      "行政拘留七日并处一千元罚款"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "张某某的外孙在幼儿园接受托育期间行走时意外摔倒",
        "original_text": "经查，8月24日，张某某(女，52岁)的外孙(男，16个月)在该幼儿园接受托育，行走间意外摔倒。",
        "entities": [
          {
            "name": "20260824",
            "type": "时间",
            "role": "摔倒发生时间"
          },
          {
            "name": "幼儿园",
            "type": "地点",
            "role": "托育机构、事发地点"
          },
          {
            "name": "张某某的外孙（男，16个月）",
            "type": "人物",
            "role": "意外摔倒的托育儿童"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E2",
        "description": "张某某到幼儿园交涉时与园方人员发生争执，抓咬撕扯致孙某某轻微伤",
        "original_text": "8月25日8时30分许，张某某到幼儿园与孙某某(女，52岁，幼儿园负责人)、马某某(女，23岁，幼儿园工作人员)交涉，发生争执后，张某某对孙某某、马某某二人抓咬、撕扯，致孙某某轻微伤。",
        "entities": [
          {
            "name": "20260825",
            "type": "时间",
            "role": "争执发生时间"
          },
          {
            "name": "张某某（女，52岁）",
            "type": "人物",
            "role": "交涉方、施害人"
          },
          {
            "name": "孙某某（女，52岁）",
            "type": "人物",
            "role": "幼儿园负责人，被抓咬致轻微伤"
          },
          {
            "name": "马某某（女，23岁）",
            "type": "人物",
            "role": "幼儿园工作人员，被撕扯"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "莱阳市公安局对张某某行政拘留七日并处罚款一千元",
        "original_text": "莱阳市公安局已依法对张某某作出行政拘留七日并处一千元罚款的处罚。",
        "entities": [
          {
            "name": "莱阳市公安局",
            "type": "机构",
            "role": "处罚机关"
          },
          {
            "name": "张某某（女，52岁）",
            "type": "人物",
            "role": "被处罚人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "经查，8月24日，张某某(女，52岁)的外孙(男，16个月)在该幼儿园接受托育，行走间意外摔倒。8月25日8时30分许，张某某到幼儿园与孙某某(女，52岁，幼儿园负责人)、马某某(女，23岁，幼儿园工作人员)交涉，发生争执后，张某某对孙某某、马某某二人抓咬、撕扯，致孙某某轻微伤。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "8月25日8时30分许，张某某到幼儿园与孙某某(女，52岁，幼儿园负责人)、马某某(女，23岁，幼儿园工作人员)交涉，发生争执后，张某某对孙某某、马某某二人抓咬、撕扯，致孙某某轻微伤。莱阳市公安局已依法对张某某作出行政拘留七日并处一千元罚款的处罚。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "幼儿意外摔倒 → 家长交涉冲突致伤 → 行政拘留罚款"
      }
    ]
  },
  {
    "news_id": "news_015",
    "url": "",
    "title": "",
    "category": "事故",
    "category_evidence": [
      "疑似触电倒地昏迷",
      "紧急将伤者送医全力救治"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "两名行人在渝中区嘉滨路人行天桥下人行道疑似触电",
        "original_text": "中新网8月26日电 据“平安渝中”微博消息，重庆市公安局渝中区分局发布警情通报称，8月25日20时35分，两名行人在渝中区嘉滨路88号人行天桥下人行道疑似触电",
        "entities": [
          {
            "name": "20260825",
            "type": "时间",
            "role": "事发时间"
          },
          {
            "name": "重庆市渝中区嘉滨路88号人行天桥下人行道",
            "type": "地点",
            "role": "事发地点"
          },
          {
            "name": "两名行人（未具名）",
            "type": "人物",
            "role": "触电者"
          }
        ],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "两名行人倒地昏迷",
        "original_text": "倒地昏迷。",
        "entities": [],
        "event_type": [
          "事故"
        ]
      },
      {
        "event_id": "E3",
        "description": "巡逻民警赶到现场，将伤者紧急送医全力救治",
        "original_text": "巡逻民警迅速赶到现场，紧急将伤者送医全力救治。",
        "entities": [
          {
            "name": "巡逻民警",
            "type": "机构",
            "role": "施救者"
          }
        ],
        "event_type": [
          "事故",
          "社会"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "possible",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.8,
        "evidence_text": "中新网8月26日电 据“平安渝中”微博消息，重庆市公安局渝中区分局发布警情通报称，8月25日20时35分，两名行人在渝中区嘉滨路88号人行天桥下人行道疑似触电倒地昏迷。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "中新网8月26日电 据“平安渝中”微博消息，重庆市公安局渝中区分局发布警情通报称，8月25日20时35分，两名行人在渝中区嘉滨路88号人行天桥下人行道疑似触电倒地昏迷。巡逻民警迅速赶到现场，紧急将伤者送医全力救治。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "疑似触电 → 倒地昏迷 → 民警送医救治"
      }
    ]
  },
  {
    "news_id": "news_016",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "发生纠纷",
      "殴打",
      "轻伤二级",
      "涉嫌故意伤害罪",
      "刑事拘留"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "金某某与陈某某在柯桥街道一KTV包厢消费娱乐期间发生纠纷",
        "original_text": "当事人金某某(女，19岁)和陈某某(男，33岁)在柯桥街道一KTV包厢消费娱乐期间发生纠纷，",
        "entities": [
          {
            "name": "20260816",
            "type": "时间",
            "role": "事发时间"
          },
          {
            "name": "绍兴市柯桥街道一KTV包厢",
            "type": "地点",
            "role": "事发地点"
          },
          {
            "name": "金某某（女，19岁）",
            "type": "人物",
            "role": "纠纷当事人"
          },
          {
            "name": "陈某某（男，33岁）",
            "type": "人物",
            "role": "纠纷当事人"
          }
        ],
        "event_type": [
          "社会"
        ]
      },
      {
        "event_id": "E2",
        "description": "陈某某在包厢厕所内殴打金某某，致其头部受伤构成轻伤二级",
        "original_text": "后陈某某在包厢厕所内殴打金某某，",
        "entities": [
          {
            "name": "陈某某（男，33岁）",
            "type": "人物",
            "role": "施暴者"
          },
          {
            "name": "金某某（女，19岁）",
            "type": "人物",
            "role": "受害人"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "公安机关介入调查并于当日将嫌疑人陈某某抓获",
        "original_text": "公安机关立即介入调查并于当日将嫌疑人陈某某抓获。",
        "entities": [
          {
            "name": "绍兴市公安局柯桥区分局",
            "type": "机构",
            "role": "侦办机关"
          },
          {
            "name": "陈某某（男，33岁）",
            "type": "人物",
            "role": "被抓获嫌疑人"
          }
        ],
        "event_type": [
          "法律"
        ]
      },
      {
        "event_id": "E4",
        "description": "陈某某因涉嫌故意伤害罪被依法刑事拘留",
        "original_text": "目前，陈某某因涉嫌故意伤害罪已被依法刑事拘留，案件正在进一步侦办中。",
        "entities": [
          {
            "name": "陈某某（男，33岁）",
            "type": "人物",
            "role": "被刑事拘留人"
          }
        ],
        "event_type": [
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "经查，8月16日凌晨，当事人金某某(女，19岁)和陈某某(男，33岁)在柯桥街道一KTV包厢消费娱乐期间发生纠纷，后陈某某在包厢厕所内殴打金某某，致金某某头部受伤。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "2026年8月16日6时许，绍兴市公安局柯桥区分局接群众报警称一女子被人打伤，在医院治疗。公安机关立即介入调查并于当日将嫌疑人陈某某抓获。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C1",
        "cause_event_id": "E3",
        "effect_event_id": "E4",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "公安机关立即介入调查并于当日将嫌疑人陈某某抓获。经查，8月16日凌晨，当事人金某某(女，19岁)和陈某某(男，33岁)在柯桥街道一KTV包厢消费娱乐期间发生纠纷，后陈某某在包厢厕所内殴打金某某，致金某某头部受伤。经鉴定，金某某的损伤评定为轻伤二级。目前，陈某某因涉嫌故意伤害罪已被依法刑事拘留，案件正在进一步侦办中。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "KTV纠纷 → 殴打致轻伤二级 → 抓获 → 刑事拘留"
      }
    ]
  },
  {
    "news_id": "news_017",
    "url": "",
    "title": "",
    "category": "经济",
    "category_evidence": [
      "荷兰中央银行",
      "黄金储备",
      "地缘政治动荡加剧",
      "转移至英国伦敦"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "地缘政治动荡加剧",
        "original_text": "由于“地缘政治动荡加剧”，",
        "entities": [],
        "event_type": [
          "政治",
          "经济"
        ]
      },
      {
        "event_id": "E2",
        "description": "荷兰央行将约86吨黄金储备从美国和加拿大转移至英国伦敦",
        "original_text": "已将其约86吨黄金储备从美国和加拿大转移至英国伦敦。",
        "entities": [
          {
            "name": "20260902",
            "type": "时间",
            "role": "声明发布时间"
          },
          {
            "name": "荷兰中央银行",
            "type": "机构",
            "role": "转移决策主体"
          },
          {
            "name": "英国伦敦",
            "type": "地点",
            "role": "黄金转移目的地"
          },
          {
            "name": "美国和加拿大",
            "type": "地点",
            "role": "黄金原存放地"
          },
          {
            "name": "约86吨黄金储备",
            "type": "其他",
            "role": "转移对象"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E3",
        "description": "存放伦敦的黄金更易交易，危机情况下可被最快速度调配",
        "original_text": "据声明，存放在伦敦的黄金储备比存放在纽约和渥太华的更易于交易。声明称：“这能使荷兰央行在危机情况下以最快速度调配这些黄金。”",
        "entities": [
          {
            "name": "荷兰中央银行",
            "type": "机构",
            "role": "受益主体"
          },
          {
            "name": "伦敦",
            "type": "地点",
            "role": "黄金存放地"
          }
        ],
        "event_type": [
          "经济"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "中新网9月3日电 据英国《卫报》报道，当地时间2日，荷兰中央银行发布声明称，由于“地缘政治动荡加剧”，已将其约86吨黄金储备从美国和加拿大转移至英国伦敦。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "conditional",
        "negation": false,
        "conditions": [
          "危机情况下"
        ],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "据声明，存放在伦敦的黄金储备比存放在纽约和渥太华的更易于交易。声明称：“这能使荷兰央行在危机情况下以最快速度调配这些黄金。”"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "地缘政治动荡 → 荷兰央行黄金转移至伦敦 → 危机时可快速调配"
      }
    ]
  },
  {
    "news_id": "news_018",
    "url": "",
    "title": "",
    "category": "经济",
    "category_evidence": [
      "央行调息通知",
      "个人住房公积金贷款年利率下调0.25个百分点",
      "每月还款减少约110元"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "央行发布调息通知，下调贷款利率",
        "original_text": "根据央行调息通知，自2015年8月26日起，本市个人住房公积金贷款年利率下调0.25个百分点。",
        "entities": [
          {
            "name": "央行",
            "type": "机构",
            "role": "调息决策机构"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E2",
        "description": "自2015年8月26日起本市个人住房公积金贷款年利率下调0.25个百分点",
        "original_text": "据本市住房公积金管理中心人士介绍，按照新利率水平，五年期以下(含五年)贷款年利率从3%下调至2.75%，五年期以上贷款年利率从3.5%下调至3.25%。",
        "entities": [
          {
            "name": "20150826",
            "type": "时间",
            "role": "新利率执行时间"
          },
          {
            "name": "本市",
            "type": "地点",
            "role": "政策适用城市"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E3",
        "description": "降息后借款人月供减少，80万元30年期贷款每月少还约110元",
        "original_text": "以住房公积金贷款额80万元、贷款30年、等额本息还款方式为例，降息前月还款额为3592.36元，降息后月还款额为3481.65元，降息后借款人每月少还110.71元，30年总共减少利息支出39855.6元。",
        "entities": [
          {
            "name": "借款人（未具名）",
            "type": "人物",
            "role": "月供减少者"
          },
          {
            "name": "住房公积金贷款（80万元、30年期）",
            "type": "其他",
            "role": "降息测算案例"
          }
        ],
        "event_type": [
          "经济"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "根据央行调息通知，自2015年8月26日起，本市个人住房公积金贷款年利率下调0.25个百分点。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "据本市住房公积金管理中心人士介绍，按照新利率水平，五年期以下(含五年)贷款年利率从3%下调至2.75%，五年期以上贷款年利率从3.5%下调至3.25%。以住房公积金贷款额80万元、贷款30年、等额本息还款方式为例，降息前月还款额为3592.36元，降息后月还款额为3481.65元，降息后借款人每月少还110.71元，30年总共减少利息支出39855.6元。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "央行调息 → 公积金贷款利率下调 → 借款人月供减少"
      }
    ]
  },
  {
    "news_id": "news_019",
    "url": "",
    "title": "",
    "category": "经济",
    "category_evidence": [
      "公积金降息细则",
      "个人住房公积金贷款年利率下调0.25个百分点",
      "每月少还100.1元"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "央行发布调息通知，下调贷款利率",
        "original_text": "根据央行调息通知，",
        "entities": [
          {
            "name": "央行",
            "type": "机构",
            "role": "调息决策机构"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E2",
        "description": "自2015年5月11日起本市个人住房公积金贷款年利率下调0.25个百分点",
        "original_text": "自2015年5月11日起，我市个人住房公积金贷款年利率下调0.25个百分点，",
        "entities": [
          {
            "name": "20150511",
            "type": "时间",
            "role": "新利率执行时间"
          },
          {
            "name": "本市",
            "type": "地点",
            "role": "政策适用城市"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E3",
        "description": "降息后借款人月供减少，70万元30年期贷款每月少还100.1元",
        "original_text": "该中心人士以住房公积金贷款额70万元，贷款30年，等额本息还款方式为例解释：降息前月还款额为3341.91元，降息后月还款额为3241.81元，降息后借款人每月少还100.1元，30年总共减少利息支出36036元。",
        "entities": [
          {
            "name": "借款人（未具名）",
            "type": "人物",
            "role": "月供减少者"
          },
          {
            "name": "住房公积金贷款（70万元、30年期）",
            "type": "其他",
            "role": "降息测算案例"
          }
        ],
        "event_type": [
          "经济"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "据悉，根据央行调息通知，自2015年5月11日起，我市个人住房公积金贷款年利率下调0.25个百分点，五年期以下(含五年)贷款年利率从3.5%调整为3.25%，五年期以上贷款年利率从4%调整为3.75%。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "该中心人士以住房公积金贷款额70万元，贷款30年，等额本息还款方式为例解释：降息前月还款额为3341.91元，降息后月还款额为3241.81元，降息后借款人每月少还100.1元，30年总共减少利息支出36036元。与商业按揭贷款相比，同样以贷款70万元，贷款30年，等额本息还款方式为例，降息后住房公积金贷款月还款额为3241.81元，按揭贷款月还款额4040.65元，住房公积金贷款每月还款额比按揭贷款少798.84元，30年总共少支出利息287582.4元。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "央行调息 → 公积金贷款利率下调 → 借款人月供减少"
      }
    ]
  },
  {
    "news_id": "news_020",
    "url": "",
    "title": "",
    "category": "经济",
    "category_evidence": [
      "财政部、国家税务总局",
      "股息红利所得",
      "个人所得税",
      "20%税率",
      "暂免征收"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "中国自1994年起对外籍个人股息红利所得暂免征收个人所得税",
        "original_text": "为促进改革开放、吸引外商投资，中国自1994年起对外籍个人从外商投资企业取得的股息红利所得暂免征收个人所得税。这项政策在改革开放初期对吸引外资发挥了积极作用。",
        "entities": [
          {
            "name": "19940101",
            "type": "时间",
            "role": "暂免征税政策起始时间（1994年）"
          },
          {
            "name": "外籍个人",
            "type": "人物",
            "role": "政策适用对象"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E2",
        "description": "财政部、税务总局公告自2026年9月1日起对外籍个人股息红利所得按20%税率征收个税",
        "original_text": "中新社北京9月1日电(记者赵建华)中国财政部、国家税务总局9月1日发布公告，明确外籍个人股息红利个人所得税政策有关事项。自2026年9月1日起，外籍个人从外商投资企业取得的股息红利所得，按照“利息、股息、红利所得”缴纳个人所得税，适用20%税率。",
        "entities": [
          {
            "name": "20260901",
            "type": "时间",
            "role": "新政策执行时间"
          },
          {
            "name": "中国财政部、国家税务总局",
            "type": "机构",
            "role": "公告发布机关"
          },
          {
            "name": "外籍个人",
            "type": "人物",
            "role": "纳税义务人"
          },
          {
            "name": "外商投资企业",
            "type": "机构",
            "role": "股息红利支付及扣缴义务人"
          }
        ],
        "event_type": [
          "经济",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "取消暂免政策有助于营造公平竞争市场环境、主张税收权益并防止税收套利",
        "original_text": "李旭红表示，对外籍个人从外商投资企业取得的股息红利所得征缴20%个人所得税，主张了中国的税收权益，避免中国税收流失；有利于防范税收漏洞，避免一些投资者通过转换企业性质获得税收套利。",
        "entities": [],
        "event_type": [
          "经济"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "indirect",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.7,
        "evidence_text": "为促进改革开放、吸引外商投资，中国自1994年起对外籍个人从外商投资企业取得的股息红利所得暂免征收个人所得税。这项政策在改革开放初期对吸引外资发挥了积极作用。如今，取消这项政策，有助于营造公平竞争的市场环境。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.8,
        "evidence_text": "李旭红表示，对外籍个人从外商投资企业取得的股息红利所得征缴20%个人所得税，主张了中国的税收权益，避免中国税收流失；有利于防范税收漏洞，避免一些投资者通过转换企业性质获得税收套利。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "1994年起免税政策 → 取消暂免改按20%征税 → 促进公平竞争、防止税收流失"
      }
    ]
  },
  {
    "news_id": "news_021",
    "url": "",
    "title": "",
    "category": "经济",
    "category_evidence": [
      "上市银行",
      "归母净利润",
      "净息差",
      "同比增速"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "存量存款重定价效应逐步消退",
        "original_text": "随着存量存款重定价效应逐步消退，",
        "entities": [],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E2",
        "description": "二季度商业银行净息差迎来四年来首次小幅抬升",
        "original_text": "二季度商业银行净息差迎来四年来首次小幅抬升，市场期盼已久的拐点信号显现，但修复进程仍在持续，42家上市银行中，净息差同比实现改善的机构不足半数，城农商行成为修复的主要力量，仍有23家银行继续面临净息差收窄的压力。",
        "entities": [
          {
            "name": "二季度",
            "type": "时间",
            "role": "净息差抬升发生的季度"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E3",
        "description": "42家上市银行上半年归母净利润合计1.13万亿元，同比增长约2.96%，盈利分化显著",
        "original_text": "2026年半年报收官，A股42家上市银行交出了总额1.13万亿元的归母净利润答卷，约2.96%的同比增速勾勒出行业大盘稳中有进的底色。8月30日，北京商报记者统计发现，总量之下，42家银行盈利呈现显著的分化格局：增速最高超18%，最低下滑超24%；其中36家银行归母净利润实现正增长，另有6家出现负增长。",
        "entities": [
          {
            "name": "20260830",
            "type": "时间",
            "role": "统计报道时间"
          },
          {
            "name": "A股42家上市银行",
            "type": "机构",
            "role": "统计对象"
          }
        ],
        "event_type": [
          "经济"
        ]
      },
      {
        "event_id": "E4",
        "description": "下半年银行业盈利水平与净息差的分化态势预计将继续",
        "original_text": "银行业盈利水平与净息差的分化态势还将继续上演。",
        "entities": [],
        "event_type": [
          "经济"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "indirect",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.7,
        "evidence_text": "二季度商业银行净息差迎来四年来首次小幅抬升，市场期盼已久的拐点信号显现，但修复进程仍在持续，42家上市银行中，净息差同比实现改善的机构不足半数，城农商行成为修复的主要力量，仍有23家银行继续面临净息差收窄的压力。随着存量存款重定价效应逐步消退，下半年，银行业盈利水平与净息差的分化态势还将继续上演。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "indirect",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.7,
        "evidence_text": "2026年半年报收官，A股42家上市银行交出了总额1.13万亿元的归母净利润答卷，约2.96%的同比增速勾勒出行业大盘稳中有进的底色。8月30日，北京商报记者统计发现，总量之下，42家银行盈利呈现显著的分化格局：增速最高超18%，最低下滑超24%；其中36家银行归母净利润实现正增长，另有6家出现负增长。二季度商业银行净息差迎来四年来首次小幅抬升，市场期盼已久的拐点信号显现，但修复进程仍在持续，42家上市银行中，净息差同比实现改善的机构不足半数，城农商行成为修复的主要力量，仍有23家银行继续面临净息差收窄的压力。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E4",
        "type": "direct",
        "modality": "possible",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.8,
        "evidence_text": "随着存量存款重定价效应逐步消退，下半年，银行业盈利水平与净息差的分化态势还将继续上演。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "存款重定价效应消退 → 净息差首次抬升 → 上市银行盈利稳中有进但分化"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "存款重定价效应消退 → 下半年分化态势继续"
      }
    ]
  },
  {
    "news_id": "news_022",
    "url": "",
    "title": "",
    "category": "社会",
    "category_evidence": [
      "遭枪击身亡",
      "认错人",
      "嫌疑人逃离现场",
      "新南威尔士州警察局长"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "凌晨闯入者冲进马尔科·塔皮亚在悉尼的住宅并开枪袭击",
        "original_text": "据报道，当地时间9月1凌晨，马尔科·塔皮亚正在床上睡觉，闯入者冲进了他的家中。",
        "entities": [
          {
            "name": "20260901",
            "type": "时间",
            "role": "案发时间"
          },
          {
            "name": "澳大利亚悉尼一处住宅",
            "type": "地点",
            "role": "案发地点"
          },
          {
            "name": "马尔科·塔皮亚（23岁大学生）",
            "type": "人物",
            "role": "受害人"
          },
          {
            "name": "闯入者（未具名）",
            "type": "人物",
            "role": "行凶嫌疑人"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E2",
        "description": "马尔科·塔皮亚遭枪击当场死亡",
        "original_text": "警方称，这名就读于悉尼科技大学的学生，遭到枪击，当场死亡。",
        "entities": [
          {
            "name": "马尔科·塔皮亚（23岁大学生）",
            "type": "人物",
            "role": "死者"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      },
      {
        "event_id": "E3",
        "description": "多名嫌疑人在警员抵达前逃离现场",
        "original_text": "新南威尔士州警方表示，多名嫌疑人在警员抵达前逃离现场。",
        "entities": [
          {
            "name": "多名嫌疑人（未具名）",
            "type": "人物",
            "role": "在逃人员"
          }
        ],
        "event_type": [
          "法律"
        ]
      },
      {
        "event_id": "E4",
        "description": "警方表示该袭击可能是“认错人”事件，正在考虑所有可能性",
        "original_text": "报道称，事发后，一名“黑帮人物”伊扎亚·乌泰在社交媒体上发文称袭击者“杀错了人，甚至没找对房子”。当被问及上述社交媒体帖文是否与这起枪击案有关，以及案件是否存在“认错人”的可能时，警方没有排除这一可能，并表示“正在考虑所有可能性”。",
        "entities": [
          {
            "name": "新南威尔士州警方",
            "type": "机构",
            "role": "调查与通报机构"
          },
          {
            "name": "伊扎亚·乌泰",
            "type": "人物",
            "role": "发帖称袭击者杀错人的“黑帮人物”"
          }
        ],
        "event_type": [
          "社会",
          "法律"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "据报道，当地时间9月1凌晨，马尔科·塔皮亚正在床上睡觉，闯入者冲进了他的家中。警方称，这名就读于悉尼科技大学的学生，遭到枪击，当场死亡。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "据报道，当地时间9月1凌晨，马尔科·塔皮亚正在床上睡觉，闯入者冲进了他的家中。警方称，这名就读于悉尼科技大学的学生，遭到枪击，当场死亡。新南威尔士州警方表示，多名嫌疑人在警员抵达前逃离现场。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C3",
        "cause_event_id": "E1",
        "effect_event_id": "E4",
        "type": "indirect",
        "modality": "possible",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.75,
        "evidence_text": "报道称，事发后，一名“黑帮人物”伊扎亚·乌泰在社交媒体上发文称袭击者“杀错了人，甚至没找对房子”。当被问及上述社交媒体帖文是否与这起枪击案有关，以及案件是否存在“认错人”的可能时，警方没有排除这一可能，并表示“正在考虑所有可能性”。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "闯入者开枪袭击 → 塔皮亚当场死亡"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "枪击作案 → 嫌疑人逃离现场"
      },
      {
        "chain_id": "C3",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "枪击事件 → 警方研判可能是认错人"
      }
    ]
  },
  {
    "news_id": "news_023",
    "url": "",
    "title": "",
    "category": "健康",
    "category_evidence": [
      "埃博拉疫情",
      "累计死亡病例超过3000例",
      "6206例确诊病例",
      "疫情暴发"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "5月15日刚果（金）埃博拉疫情暴发，初期涉及1个省的2个卫生区",
        "original_text": "5月15日疫情暴发时，仅涉及1个省的2个卫生区，",
        "entities": [
          {
            "name": "20260515",
            "type": "时间",
            "role": "疫情暴发时间"
          },
          {
            "name": "刚果（金）",
            "type": "地点",
            "role": "疫情发生国"
          }
        ],
        "event_type": [
          "健康"
        ]
      },
      {
        "event_id": "E2",
        "description": "疫情扩散至6个省的60个卫生区、约24万平方公里",
        "original_text": "目前已扩散至6个省的60个卫生区、约24万平方公里。",
        "entities": [
          {
            "name": "刚果（金）6个省的60个卫生区",
            "type": "地点",
            "role": "疫情扩散范围"
          }
        ],
        "event_type": [
          "健康"
        ]
      },
      {
        "event_id": "E3",
        "description": "疫情累计报告6206例确诊病例，其中3009人死亡",
        "original_text": "非洲疾控中心最新数据显示，自今年5月疫情暴发以来，刚果(金)已累计报告6206例确诊病例，其中3009人死亡。",
        "entities": [
          {
            "name": "非洲疾病预防控制中心",
            "type": "机构",
            "role": "数据发布机构"
          }
        ],
        "event_type": [
          "健康"
        ]
      },
      {
        "event_id": "E4",
        "description": "涉疫情高风险地区学校本周复课",
        "original_text": "涉疫情高风险地区学校本周复课。",
        "entities": [
          {
            "name": "本周",
            "type": "时间",
            "role": "复课时间（相对表述）"
          },
          {
            "name": "涉疫情高风险地区",
            "type": "地点",
            "role": "复课地区"
          }
        ],
        "event_type": [
          "健康",
          "社会"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "非洲疾控中心主任让·卡塞亚表示，5月15日疫情暴发时，仅涉及1个省的2个卫生区，目前已扩散至6个省的60个卫生区、约24万平方公里。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C1",
        "cause_event_id": "E2",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.85,
        "evidence_text": "非洲疾控中心最新数据显示，自今年5月疫情暴发以来，刚果(金)已累计报告6206例确诊病例，其中3009人死亡。非洲疾控中心主任让·卡塞亚表示，5月15日疫情暴发时，仅涉及1个省的2个卫生区，目前已扩散至6个省的60个卫生区、约24万平方公里。"
      },
      {
        "relation_id": "R3",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E4",
        "type": "indirect",
        "modality": "possible",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.6,
        "evidence_text": "中新社约翰内斯堡9月2日电 非洲疾病预防控制中心2日表示，刚果(金)本轮埃博拉疫情累计死亡病例超过3000例；涉疫情高风险地区学校本周复课。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "埃博拉疫情暴发 → 疫情扩散 → 6206例确诊、3009人死亡"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E4",
        "description": "疫情演变 → 高风险地区学校复课"
      }
    ]
  },
  {
    "news_id": "news_024",
    "url": "",
    "title": "",
    "category": "环境",
    "category_evidence": [
      "泥石流灾害",
      "16人遇难，546人失联",
      "抢险救灾"
    ],
    "events": [
      {
        "event_id": "E1",
        "description": "西藏吉隆县发生“8·26”泥石流灾害",
        "original_text": "8月30日，西藏自治区人民政府新闻办公室在日喀则市举行新闻发布会，介绍吉隆县泥石流灾害抢险救灾有关情况。",
        "entities": [
          {
            "name": "20260826",
            "type": "时间",
            "role": "灾害发生时间"
          },
          {
            "name": "西藏自治区日喀则市吉隆县",
            "type": "地点",
            "role": "灾害发生地"
          }
        ],
        "event_type": [
          "环境",
          "事故"
        ]
      },
      {
        "event_id": "E2",
        "description": "泥石流灾害造成16人遇难、546人失联",
        "original_text": "截至29日18时，灾害造成16人遇难，546人失联。",
        "entities": [
          {
            "name": "20260829",
            "type": "时间",
            "role": "伤亡统计截止时间"
          }
        ],
        "event_type": [
          "环境",
          "事故"
        ]
      },
      {
        "event_id": "E3",
        "description": "灾后抢险救援工作加速推进",
        "original_text": "灾后抢险救援工作加速推进。",
        "entities": [
          {
            "name": "吉隆县“8·26”泥石流灾害应急救援指挥部",
            "type": "机构",
            "role": "救援指挥机构"
          }
        ],
        "event_type": [
          "环境",
          "事故",
          "社会"
        ]
      }
    ],
    "causal_relations": [
      {
        "relation_id": "R1",
        "chain_id": "C1",
        "cause_event_id": "E1",
        "effect_event_id": "E2",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.95,
        "evidence_text": "新华社西藏吉隆8月30日电（记者杨守勇、李键）30日，西藏自治区人民政府新闻办公室在吉隆县吉隆镇举行新闻发布会，自治区主席、吉隆县“8·26”泥石流灾害应急救援指挥部指挥长嘎玛泽登表示，截至29日18时，灾害造成16人遇难，546人失联。"
      },
      {
        "relation_id": "R2",
        "chain_id": "C2",
        "cause_event_id": "E1",
        "effect_event_id": "E3",
        "type": "direct",
        "modality": "factual",
        "negation": false,
        "conditions": [],
        "counterfactual_marker": false,
        "confidence": 0.9,
        "evidence_text": "8月30日，西藏自治区人民政府新闻办公室在日喀则市举行新闻发布会，介绍吉隆县泥石流灾害抢险救灾有关情况。新华社记者旦增尼玛曲珠摄新华社西藏吉隆8月30日电（记者杨守勇、李键）30日，西藏自治区人民政府新闻办公室在吉隆县吉隆镇举行新闻发布会，自治区主席、吉隆县“8·26”泥石流灾害应急救援指挥部指挥长嘎玛泽登表示，截至29日18时，灾害造成16人遇难，546人失联。灾后抢险救援工作加速推进。"
      }
    ],
    "chains": [
      {
        "chain_id": "C1",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E2",
        "description": "泥石流灾害 → 16人遇难、546人失联"
      },
      {
        "chain_id": "C2",
        "root_cause_event_id": "E1",
        "final_effect_event_id": "E3",
        "description": "泥石流灾害 → 抢险救援加速推进"
      }
    ]
  }
];
