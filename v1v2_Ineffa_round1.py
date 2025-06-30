import json
import csv
import os
from datetime import datetime

# 全局参数
citiaoshu = 30
max_crit = 24  # 双暴词条上限

# 角色配置
character_name = "伊涅芙"
character_base = 330
character_atk = 0.0
character_em = 0
character_cr = 0.242
character_cd = 0.5
character_enhanced = 0.0
character_lunar_enhanced = 0.0

# 角色伤害倍率
character_passive_mult = 0.8
character_skill_initial_mult = 1.5552
character_skill_dot_mult = 2.304
character_burst_mult = 12.1824

# 伤害次数
hit_num_lunar = 9
hit_num_passive = 9
hit_num_skill_initial = 1
hit_num_skill_dot = 9
hit_num_burst = 1

# 抗性和敌人等级
RES = 0.9
enemy_level = 100

# 词条数值转换
CONVERSION = {
    'ATK': 0.05,
    'EM': 20.0,
    'CR': 0.033,
    'CD': 0.066
}

# 圣遗物配置
ARTIFACT_CONFIGS = {
    "精精暴": {
        "atk_bonus": 0.0,
        "em_bonus": 373.0,  # 186.5 * 2
        "enhanced_bonus": 0.0
    },
    "精攻暴": {
        "atk_bonus": 0.466,
        "em_bonus": 186.5,
        "enhanced_bonus": 0.0
    },
    "攻攻暴": {
        "atk_bonus": 0.932,  # 0.466 * 2
        "em_bonus": 0,
        "enhanced_bonus": 0.0
    },
    "攻伤暴": {
        "atk_bonus": 0.466,
        "em_bonus": 0,
        "enhanced_bonus": 0.466
    }
}

# 默认武器配置
DEFAULT_WEAPONS = [
    {
        "name": "支离轮光",
        "base": 608,
        "atk": 0.24,
        "em": 0,
        "cr": 0.0,
        "cd": 0.662,
        "enhanced": 0.0,
        "lunar_enhanced": 0.40
    }
]

# 默认圣遗物套装配置
DEFAULT_ARTISETS = [
    {
        "name": "饰金之梦",
        "atk": 0.14,
        "em": 180,
        "cr": 0.0,
        "cd": 0.0,
        "enhanced": 0.0,
        "lunar_enhanced": 0.0
    }
]

def generate_allocations(citiaoshu, max_crit):
    """生成所有词条分配方案（0.5单位精度），并添加双暴词条限制"""
    total_steps = citiaoshu * 2  # 将28个完整词条转换为56个0.5单位词条
    max_crit_steps = max_crit * 2  # 将双暴上限转换为0.5单位
    allocations = []
    
    # 遍历所有可能的攻击力词条数（0.5为单位）
    for atk_steps in range(0, total_steps + 1):
        # 遍历所有可能的元素精通词条数（0.5为单位）
        for em_steps in range(0, total_steps + 1 - atk_steps):
            # 剩余词条分配给双暴
            remaining_steps = total_steps - atk_steps - em_steps
            
            # 遍历所有可能的暴击率词条数（0.5为单位）
            for cr_steps in range(0, remaining_steps + 1):
                cd_steps = remaining_steps - cr_steps
                
                # 检查双暴词条总数是否超过限制
                total_crit_steps = cr_steps + cd_steps
                if total_crit_steps > max_crit_steps:
                    continue  # 跳过超过限制的分配
                
                # 转换为0.5单位
                allocations.append((
                    atk_steps * 0.5, 
                    em_steps * 0.5, 
                    cr_steps * 0.5, 
                    cd_steps * 0.5
                ))
    return allocations

def calculate_dmg(alloc, config_name, weapon, artiset):
    """计算伤害"""
    config = ARTIFACT_CONFIGS[config_name]
    atk, em, cr, cd = alloc

    # 反应基数*队友系数
    reaction_base = 1446.85 * 0.6

    # 攻击力计算
    base_atk_value = (character_base + weapon["base"]) * (
        1 + character_atk + weapon["atk"] + atk * CONVERSION['ATK'] + config["atk_bonus"] + artiset["atk"]
    ) + 311

    # 元素精通计算
    base_em_value = (
        em * CONVERSION['EM'] + 
        artiset["em"] +
        weapon["em"] + 
        character_em + 
        config["em_bonus"]
    )
    extra_em_value = base_atk_value * 0.06  # 不可二次转化元素精通
    em_value = base_em_value + extra_em_value  # 面板元素精通

    # 特殊武器处理（不可二次转化攻击）
    if weapon["name"] == "赤沙之杖（0层）":
        # 赤沙之杖0层特殊处理
        extra_atk_value = base_em_value * 0.52
    elif weapon["name"] == "赤沙之杖（1层）":
        # 赤沙之杖1层特殊处理
        extra_atk_value = base_em_value * (0.52 + 0.28)
    elif weapon["name"] == "赤沙之杖（2层）":
        # 赤沙之杖2层特殊处理
        extra_atk_value = base_em_value * (0.52 + 0.28 * 2)
    elif weapon["name"] == "赤沙之杖（3层）":
        # 赤沙之杖3层特殊处理
        extra_atk_value = base_em_value * (0.52 + 0.28 * 3)
    elif weapon["name"] == "护摩之杖（满血）":
        # 护摩之杖满血特殊处理
        extra_atk_value = (12613 * 1.2 + 4780) * 0.008
    elif weapon["name"] == "护摩之杖（半血）":
        # 护摩之杖半血特殊处理
        extra_atk_value = (12613 * 1.2 + 4780) * 0.018
    elif weapon["name"] == "薙草之稻光":
        # 薙草之稻光特殊处理
        extra_atk_value = 0.851 * 0.28
    else:
        # 其他武器默认处理
        extra_atk_value = 0

    final_atk_value = base_atk_value + extra_atk_value  # 面板攻击力

    # 基础区加成
    base_enhanced = 1 + min(0.14, base_atk_value / 100 * 0.007)

    # 增伤区
    enhanced = (1 + artiset["enhanced"] + weapon["enhanced"] + character_enhanced + config["enhanced_bonus"])

    # 月增伤区
    lunar_enhanced = (1 + 5 * em_value / (2100 + em_value) + artiset["lunar_enhanced"] + weapon["lunar_enhanced"] + character_lunar_enhanced)

    # 暴击区
    crit_rate = min(1, artiset["cr"] + weapon["cr"] + character_cr + cr * CONVERSION['CR'] + 0.311)
    crit_dmg = artiset["cd"] + weapon["cd"] + character_cd + cd * CONVERSION['CD']
    crit_multiplier = 1 + crit_rate * crit_dmg

    # 抗性区
    res = RES

    # 防御区
    defense_value = 190 / (190 + (100 + enemy_level))

    # ========== 伤害计算 ==========
    # 剧变月感电伤害
    transformative_lunar_dmg = 3 * reaction_base * base_enhanced * lunar_enhanced * crit_multiplier * res
    
    # 直伤月感电伤害
    direct_lunar_dmg = 3 * final_atk_value * character_passive_mult * base_enhanced * lunar_enhanced * crit_multiplier * res
    
    # E技能初始伤害
    skill_initial_dmg = final_atk_value * character_skill_initial_mult * enhanced * crit_multiplier * res * defense_value
    
    # E技能持续伤害
    skill_dot_dmg = final_atk_value * character_skill_dot_mult * enhanced * crit_multiplier * res * defense_value
    
    # Q技能爆发伤害
    burst_dmg = final_atk_value * character_burst_mult * enhanced * crit_multiplier * res * defense_value

    # 总伤害计算
    total_dmg = (
        transformative_lunar_dmg * hit_num_lunar + 
        direct_lunar_dmg * hit_num_passive + 
        skill_initial_dmg * hit_num_skill_initial + 
        skill_dot_dmg * hit_num_skill_dot + 
        burst_dmg * hit_num_burst
    )
    
    return (
        total_dmg, 
        transformative_lunar_dmg, 
        direct_lunar_dmg, 
        skill_initial_dmg, 
        skill_dot_dmg, 
        burst_dmg, 
        final_atk_value, 
        em_value, 
        crit_rate, 
        crit_dmg
    )

def find_optimal_allocation(config_name, weapon, artiset):
    """寻找最优分配方案"""
    allocations = generate_allocations(citiaoshu, max_crit)
    max_dmg = 0
    best_alloc = None
    best_stats = None
    
    for alloc in allocations:
        result = calculate_dmg(alloc, config_name, weapon, artiset)
        total_dmg = result[0]
        
        if total_dmg > max_dmg:
            max_dmg = total_dmg
            best_alloc = alloc
            best_stats = result
    
    return best_alloc, best_stats, max_dmg

def load_config_with_default(filename, default_config):
    """加载配置，如果文件不存在则使用默认配置"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 加载 {filename} 时出错 ({e})，使用默认配置")
            return default_config
    else:
        print(f"注意: {filename} 文件不存在，使用默认配置")
        return default_config

def main():
    # 加载武器和圣遗物配置（使用默认配置作为后备）
    weapons = load_config_with_default('weapons.json', DEFAULT_WEAPONS)
    artisets = load_config_with_default('artisets.json', DEFAULT_ARTISETS)
    
    # 自动生成所有武器+圣遗物组合
    configs = []
    for weapon in weapons:
        for artiset in artisets:
            configs.append({
                "weapon": weapon,
                "artiset": artiset
            })
    
    print("圣遗物主词条配置比较（词条分配精度：0.5，双暴词条上限：24）")
    print("=" * 85)
    print(f"总词条数: {citiaoshu} | 双暴词条上限: {max_crit}")
    
    # 准备CSV文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"artifact_results_{timestamp}.csv"
    
    # CSV表头
    csv_headers = [
        '武器', '圣遗物套装', '主词条配置', ' ',
        '攻击力词条', '元素精通词条', '暴击率词条', '暴击伤害词条', '双暴总词条', ' ',
        '攻击力', '元素精通', '暴击率', '暴击伤害', ' ',
        '剧变月感电伤害单段', '直伤月感电伤害单段', 'E技能持续伤害单段', ' ',
        '剧变月感电伤害', '直伤月感电伤害', 'E技能释放伤害', 'E技能持续伤害', 'Q技能爆发伤害', '总伤害', ' ',
        '是否本组合最优'
    ]
    
    all_rows = []
    global_best_dmg = 0
    
    for config in configs:
        weapon = config["weapon"]
        artiset = config["artiset"]
        set_name = artiset["name"]
        weapon_name = weapon["name"]
        
        print("=" * 85)
        print(f"武器: {weapon_name} | 圣遗物套装: {set_name} | 角色: {character_name}")
        print("=" * 85)
        
        results = {}
        for config_name in ARTIFACT_CONFIGS:
            best_alloc, best_stats, total_dmg = find_optimal_allocation(config_name, weapon, artiset)
            results[config_name] = {
                "alloc": best_alloc,
                "stats": best_stats,
                "total_dmg": total_dmg
            }
        
        # 找出当前武器+圣遗物组合的最优配置
        best_in_group = max(results.items(), key=lambda x: x[1]["total_dmg"])
        best_group_dmg = best_in_group[1]["total_dmg"]
        
        # 更新全局最优
        if best_group_dmg > global_best_dmg:
            global_best_dmg = best_group_dmg
        
        # 收集结果并输出
        for config_name, data in results.items():
            alloc = data["alloc"]
            (
                total_dmg, 
                transformative_lunar_dmg, 
                direct_lunar_dmg, 
                skill_initial_dmg, 
                skill_dot_dmg, 
                burst_dmg, 
                atk_value, 
                em_value, 
                crit_rate, 
                crit_dmg
            ) = data["stats"]
            
            # 计算双暴词条总数
            total_crit = alloc[2] + alloc[3]
            
            # 输出到控制台
            print(f"=== {config_name} 最优词条分配 ===")
            print(f"| 攻击力: {alloc[0]:.1f}词条 | 元素精通: {alloc[1]:.1f}词条 | 暴击率: {alloc[2]:.1f}词条 | 暴击伤害: {alloc[3]:.1f}词条 | 双暴总词条: {total_crit:.1f} (上限: {max_crit}) |")
            
            print("\n面板属性:")
            print(f"| 攻击力: {atk_value:.2f} | 元素精通: {em_value:.2f} | 暴击率: {crit_rate:.4f} | 暴击伤害: {crit_dmg:.4f} |")
            
            print("\n伤害明细:")
            print(f"- 剧变月感电:     {transformative_lunar_dmg:.2f} × {hit_num_lunar} = {transformative_lunar_dmg * hit_num_lunar:.2f}")
            print(f"- 直伤月感电:     {direct_lunar_dmg:.2f} × {hit_num_passive} = {direct_lunar_dmg * hit_num_passive:.2f}")
            print(f"- E技能释放:      {skill_initial_dmg:.2f} × {hit_num_skill_initial} = {skill_initial_dmg * hit_num_skill_initial:.2f}")
            print(f"- E技能持续:      {skill_dot_dmg:.2f} × {hit_num_skill_dot} = {skill_dot_dmg * hit_num_skill_dot:.2f}")
            print(f"- Q技能爆发:      {burst_dmg:.2f} × {hit_num_burst} = {burst_dmg * hit_num_burst:.2f}")
            
            print(f"\n总伤害:           {total_dmg:.2f}")
            print("=" * 85)
            
            # 准备CSV行数据
            is_group_best = (config_name == best_in_group[0])
            
            row = {
                '武器': weapon_name,
                '圣遗物套装': set_name,
                '主词条配置': config_name,

                '攻击力词条': f"{alloc[0]:.1f}",
                '元素精通词条': f"{alloc[1]:.1f}",
                '暴击率词条': f"{alloc[2]:.1f}",
                '暴击伤害词条': f"{alloc[3]:.1f}",
                '双暴总词条': f"{total_crit:.1f}",

                '攻击力': f"{atk_value:.2f}",
                '元素精通': f"{em_value:.2f}",
                '暴击率': f"{crit_rate:.4f}",
                '暴击伤害': f"{crit_dmg:.4f}",

                '剧变月感电伤害单段': f"{transformative_lunar_dmg:.2f}",
                '直伤月感电伤害单段': f"{direct_lunar_dmg:.2f}",
                'E技能持续伤害单段': f"{skill_dot_dmg:.2f}",

                '剧变月感电伤害': f"{transformative_lunar_dmg * hit_num_lunar:.2f}",
                '直伤月感电伤害': f"{direct_lunar_dmg * hit_num_passive:.2f}",
                'E技能释放伤害': f"{skill_initial_dmg * hit_num_skill_initial:.2f}",
                'E技能持续伤害': f"{skill_dot_dmg * hit_num_skill_dot:.2f}",
                'Q技能爆发伤害': f"{burst_dmg * hit_num_burst:.2f}",
                '总伤害': f"{total_dmg:.2f}",

                '是否本组合最优': "是" if is_group_best else "否"
            }
            all_rows.append(row)
        
        # 比较总伤害
        print(f"=== {weapon_name} + {set_name} 配置总伤害对比 ===")
        for config_name, data in results.items():
            diff = data['total_dmg'] - best_in_group[1]['total_dmg']
            print(f"{config_name}: {data['total_dmg']:.2f} (差异: {diff:+.2f})")
        
        print(f"\n最优配置: {best_in_group[0]} (总伤害: {best_in_group[1]['total_dmg']:.2f})")
        print("=" * 85)
    
    # 全局比较
    print("\n=== 全局配置总伤害对比 ===")
    for row in all_rows:
        if abs(float(row['总伤害']) - global_best_dmg) < 1:
            print(f"全局最优配置: {row['武器']} + {row['圣遗物套装']} ({row['主词条配置']}) | 总伤害: {row['总伤害']}")
    
    print("=" * 85)
    
    # 写入CSV文件
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\n结果已导出到: {csv_filename}")

if __name__ == "__main__":
    main()
