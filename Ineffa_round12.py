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
    """计算伤害（包含两轮）"""
    config = ARTIFACT_CONFIGS[config_name]
    atk, em, cr, cd = alloc

    # 反应基数*队友系数
    reaction_base = 1446.85 * 0.6

    # 攻击力计算
    base_atk_value = (character_base + weapon["base"]) * (
        1 + character_atk + weapon["atk"] + artiset["atk"] + atk * CONVERSION['ATK'] + config["atk_bonus"]
    ) + 311

    # 元素精通计算（第一轮）
    base_em_value = (
        em * CONVERSION['EM'] + 
        artiset["em"] +
        weapon["em"] + 
        character_em + 
        config["em_bonus"]
    )
    extra_em_value_round1 = base_atk_value * 0.06  # 第一轮有额外元素精通
    extra_em_value_round2 = 0  # 第二轮没有额外元素精通
    em_value_round1 = base_em_value + extra_em_value_round1  # 第一轮面板元素精通
    em_value_round2 = base_em_value + extra_em_value_round2  # 第二轮面板元素精通

    # 特殊武器处理（不可二次转化攻击）
    if weapon["name"] == "赤沙之杖（0层）":
        extra_atk_value = base_em_value * 0.52
    elif weapon["name"] == "赤沙之杖（1层）":
        extra_atk_value = base_em_value * (0.52 + 0.28)
    elif weapon["name"] == "赤沙之杖（2层）":
        extra_atk_value = base_em_value * (0.52 + 0.28 * 2)
    elif weapon["name"] == "赤沙之杖（3层）":
        extra_atk_value = base_em_value * (0.52 + 0.28 * 3)
    elif weapon["name"] == "护摩之杖（满血）":
        extra_atk_value = (12613 * 1.2 + 4780) * 0.008
    elif weapon["name"] == "护摩之杖（半血）":
        extra_atk_value = (12613 * 1.2 + 4780) * 0.018
    elif weapon["name"] == "薙草之稻光":
        extra_atk_value = 0.851 * 0.28
    else:
        # 其他武器默认处理
        extra_atk_value = 0

    final_atk_value = base_atk_value + extra_atk_value  # 面板攻击力（两轮相同）

    # 基础区加成（两轮相同）
    base_enhanced = 1 + min(0.14, base_atk_value / 100 * 0.007)

    # 增伤区（两轮相同）
    enhanced = (1 + artiset["enhanced"] + weapon["enhanced"] + character_enhanced + config["enhanced_bonus"])

    # 暴击区（两轮相同）
    crit_rate = min(1, artiset["cr"] + weapon["cr"] + character_cr + cr * CONVERSION['CR'] + 0.311)
    crit_dmg = artiset["cd"] + weapon["cd"] + character_cd + cd * CONVERSION['CD']
    crit_multiplier = 1 + crit_rate * crit_dmg

    # 抗性区（两轮相同）
    res = RES

    # 防御区（两轮相同）
    defense_value = 190 / (190 + (100 + enemy_level))

    # ========== 第一轮伤害计算 ==========
    # 月增伤区（第一轮）
    lunar_enhanced_round1 = (1 + 5 * em_value_round1 / (2100 + em_value_round1) + 
                             artiset["lunar_enhanced"] + weapon["lunar_enhanced"] + character_lunar_enhanced)
    
    # 剧变月感电伤害
    transformative_lunar_dmg_round1 = 3 * reaction_base * base_enhanced * lunar_enhanced_round1 * crit_multiplier * res
    
    # 直伤月感电伤害
    direct_lunar_dmg_round1 = 3 * final_atk_value * character_passive_mult * base_enhanced * lunar_enhanced_round1 * crit_multiplier * res
    
    # E技能初始伤害
    skill_initial_dmg_round1 = final_atk_value * character_skill_initial_mult * enhanced * crit_multiplier * res * defense_value
    
    # E技能持续伤害
    skill_dot_dmg_round1 = final_atk_value * character_skill_dot_mult * enhanced * crit_multiplier * res * defense_value
    
    # Q技能爆发伤害
    burst_dmg_round1 = final_atk_value * character_burst_mult * enhanced * crit_multiplier * res * defense_value

    # 第一轮总伤害计算
    total_dmg_round1 = (
        transformative_lunar_dmg_round1 * hit_num_lunar + 
        direct_lunar_dmg_round1 * hit_num_passive + 
        skill_initial_dmg_round1 * hit_num_skill_initial + 
        skill_dot_dmg_round1 * hit_num_skill_dot + 
        burst_dmg_round1 * hit_num_burst
    )
    
    # ========== 第二轮伤害计算 ==========
    # 月增伤区（第二轮）
    lunar_enhanced_round2 = (1 + 5 * em_value_round2 / (2100 + em_value_round2) + 
                             artiset["lunar_enhanced"] + weapon["lunar_enhanced"] + character_lunar_enhanced)
    
    # 剧变月感电伤害
    transformative_lunar_dmg_round2 = 3 * reaction_base * base_enhanced * lunar_enhanced_round2 * crit_multiplier * res
    
    # 直伤月感电伤害
    direct_lunar_dmg_round2 = 3 * final_atk_value * character_passive_mult * base_enhanced * lunar_enhanced_round2 * crit_multiplier * res
    
    # E技能初始伤害
    skill_initial_dmg_round2 = final_atk_value * character_skill_initial_mult * enhanced * crit_multiplier * res * defense_value
    
    # E技能持续伤害
    skill_dot_dmg_round2 = final_atk_value * character_skill_dot_mult * enhanced * crit_multiplier * res * defense_value
    
    # 第二轮总伤害计算（没有Q技能爆发）
    total_dmg_round2 = (
        transformative_lunar_dmg_round2 * hit_num_lunar + 
        direct_lunar_dmg_round2 * hit_num_passive + 
        skill_initial_dmg_round2 * hit_num_skill_initial + 
        skill_dot_dmg_round2 * hit_num_skill_dot
    )
    
    # 两轮总伤害
    total_dmg_both_rounds = total_dmg_round1 + total_dmg_round2
    
    return (
        # 第一轮伤害
        total_dmg_round1, 
        transformative_lunar_dmg_round1, 
        direct_lunar_dmg_round1, 
        skill_initial_dmg_round1, 
        skill_dot_dmg_round1, 
        burst_dmg_round1,
        
        # 第二轮伤害
        total_dmg_round2,
        transformative_lunar_dmg_round2, 
        direct_lunar_dmg_round2, 
        skill_initial_dmg_round2, 
        skill_dot_dmg_round2,
        
        # 面板属性
        final_atk_value, 
        em_value_round1, 
        em_value_round2, 
        crit_rate, 
        crit_dmg,
        
        # 两轮总伤害
        total_dmg_both_rounds
    )

def find_optimal_allocation(config_name, weapon, artiset):
    """寻找最优分配方案（基于两轮总伤害）"""
    allocations = generate_allocations(citiaoshu, max_crit)
    max_dmg = 0
    best_alloc = None
    best_stats = None
    
    for alloc in allocations:
        result = calculate_dmg(alloc, config_name, weapon, artiset)
        total_dmg_both_rounds = result[-1]  # 获取两轮总伤害
        
        if total_dmg_both_rounds > max_dmg:
            max_dmg = total_dmg_both_rounds
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
    
    # CSV表头（新增第二轮伤害相关字段）
    csv_headers = [
        '武器', '圣遗物套装', '主词条配置', ' ',
        '攻击力词条', '元素精通词条', '暴击率词条', '暴击伤害词条', '双暴总词条', ' ',
        '攻击力', '元素精通（第一轮）', '元素精通（第二轮）', '暴击率', '暴击伤害', ' ',
        '剧变月感电伤害单段（第一轮）', '直伤月感电伤害单段（第一轮）', 'E技能持续伤害单段（第一轮）', ' ',
        '剧变月感电伤害单段（第二轮）', '直伤月感电伤害单段（第二轮）', 'E技能持续伤害单段（第二轮）', ' ',
        '剧变月感电伤害（第一轮）', '直伤月感电伤害（第一轮）', 'E技能释放伤害（第一轮）', 
        'E技能持续伤害（第一轮）', 'Q技能爆发伤害（第一轮）', '第一轮总伤害', ' ',
        '剧变月感电伤害（第二轮）', '直伤月感电伤害（第二轮）', 'E技能释放伤害（第二轮）', 
        'E技能持续伤害（第二轮）', '第二轮总伤害', ' ',
        '两轮总伤害', '是否本组合最优'
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
            best_alloc, best_stats, total_dmg_both_rounds = find_optimal_allocation(config_name, weapon, artiset)
            results[config_name] = {
                "alloc": best_alloc,
                "stats": best_stats,
                "total_dmg_both_rounds": total_dmg_both_rounds
            }
        
        # 找出当前武器+圣遗物组合的最优配置
        best_in_group = max(results.items(), key=lambda x: x[1]["total_dmg_both_rounds"])
        best_group_dmg = best_in_group[1]["total_dmg_both_rounds"]
        
        # 更新全局最优
        if best_group_dmg > global_best_dmg:
            global_best_dmg = best_group_dmg
        
        # 收集结果并输出
        for config_name, data in results.items():
            alloc = data["alloc"]
            stats = data["stats"]
            
            # 解析统计结果
            (
                total_dmg_round1, 
                transformative_lunar_dmg_round1, 
                direct_lunar_dmg_round1, 
                skill_initial_dmg_round1, 
                skill_dot_dmg_round1, 
                burst_dmg_round1,
                total_dmg_round2,
                transformative_lunar_dmg_round2, 
                direct_lunar_dmg_round2, 
                skill_initial_dmg_round2, 
                skill_dot_dmg_round2,
                final_atk_value, 
                em_value_round1, 
                em_value_round2, 
                crit_rate, 
                crit_dmg,
                total_dmg_both_rounds
            ) = stats
            
            # 计算双暴词条总数
            total_crit = alloc[2] + alloc[3]
            
            # 输出到控制台
            print(f"=== {config_name} 最优词条分配 ===")
            print(f"| 攻击力: {alloc[0]:.1f}词条 | 元素精通: {alloc[1]:.1f}词条 | 暴击率: {alloc[2]:.1f}词条 | 暴击伤害: {alloc[3]:.1f}词条 | 双暴总词条: {total_crit:.1f} (上限: {max_crit}) |")
            
            print("\n面板属性:")
            print(f"| 攻击力: {final_atk_value:.2f} | 元素精通（第一轮）: {em_value_round1:.2f} | 元素精通（第二轮）: {em_value_round2:.2f} |")
            print(f"| 暴击率: {crit_rate:.4f} | 暴击伤害: {crit_dmg:.4f} |")
            
            print("\n第一轮伤害明细:")
            print(f"- 剧变月感电:     {transformative_lunar_dmg_round1:.2f} × {hit_num_lunar} = {transformative_lunar_dmg_round1 * hit_num_lunar:.2f}")
            print(f"- 直伤月感电:     {direct_lunar_dmg_round1:.2f} × {hit_num_passive} = {direct_lunar_dmg_round1 * hit_num_passive:.2f}")
            print(f"- E技能释放:      {skill_initial_dmg_round1:.2f} × {hit_num_skill_initial} = {skill_initial_dmg_round1 * hit_num_skill_initial:.2f}")
            print(f"- E技能持续:      {skill_dot_dmg_round1:.2f} × {hit_num_skill_dot} = {skill_dot_dmg_round1 * hit_num_skill_dot:.2f}")
            print(f"- Q技能爆发:      {burst_dmg_round1:.2f} × {hit_num_burst} = {burst_dmg_round1 * hit_num_burst:.2f}")
            print(f"第一轮总伤害:     {total_dmg_round1:.2f}")
            
            print("\n第二轮伤害明细:")
            print(f"- 剧变月感电:     {transformative_lunar_dmg_round2:.2f} × {hit_num_lunar} = {transformative_lunar_dmg_round2 * hit_num_lunar:.2f}")
            print(f"- 直伤月感电:     {direct_lunar_dmg_round2:.2f} × {hit_num_passive} = {direct_lunar_dmg_round2 * hit_num_passive:.2f}")
            print(f"- E技能释放:      {skill_initial_dmg_round2:.2f} × {hit_num_skill_initial} = {skill_initial_dmg_round2 * hit_num_skill_initial:.2f}")
            print(f"- E技能持续:      {skill_dot_dmg_round2:.2f} × {hit_num_skill_dot} = {skill_dot_dmg_round2 * hit_num_skill_dot:.2f}")
            print(f"第二轮总伤害:     {total_dmg_round2:.2f}")
            
            print(f"\n两轮总伤害:       {total_dmg_both_rounds:.2f}")
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

                '攻击力': f"{final_atk_value:.2f}",
                '元素精通（第一轮）': f"{em_value_round1:.2f}",
                '元素精通（第二轮）': f"{em_value_round2:.2f}",
                '暴击率': f"{crit_rate:.4f}",
                '暴击伤害': f"{crit_dmg:.4f}",

                '剧变月感电伤害单段（第一轮）': f"{transformative_lunar_dmg_round1:.2f}",
                '直伤月感电伤害单段（第一轮）': f"{direct_lunar_dmg_round1:.2f}",
                'E技能持续伤害单段（第一轮）': f"{skill_dot_dmg_round1:.2f}",
                
                '剧变月感电伤害单段（第二轮）': f"{transformative_lunar_dmg_round2:.2f}",
                '直伤月感电伤害单段（第二轮）': f"{direct_lunar_dmg_round2:.2f}",
                'E技能持续伤害单段（第二轮）': f"{skill_dot_dmg_round2:.2f}",

                '剧变月感电伤害（第一轮）': f"{transformative_lunar_dmg_round1 * hit_num_lunar:.2f}",
                '直伤月感电伤害（第一轮）': f"{direct_lunar_dmg_round1 * hit_num_passive:.2f}",
                'E技能释放伤害（第一轮）': f"{skill_initial_dmg_round1 * hit_num_skill_initial:.2f}",
                'E技能持续伤害（第一轮）': f"{skill_dot_dmg_round1 * hit_num_skill_dot:.2f}",
                'Q技能爆发伤害（第一轮）': f"{burst_dmg_round1 * hit_num_burst:.2f}",
                '第一轮总伤害': f"{total_dmg_round1:.2f}",
                
                '剧变月感电伤害（第二轮）': f"{transformative_lunar_dmg_round2 * hit_num_lunar:.2f}",
                '直伤月感电伤害（第二轮）': f"{direct_lunar_dmg_round2 * hit_num_passive:.2f}",
                'E技能释放伤害（第二轮）': f"{skill_initial_dmg_round2 * hit_num_skill_initial:.2f}",
                'E技能持续伤害（第二轮）': f"{skill_dot_dmg_round2 * hit_num_skill_dot:.2f}",
                '第二轮总伤害': f"{total_dmg_round2:.2f}",
                
                '两轮总伤害': f"{total_dmg_both_rounds:.2f}",
                '是否本组合最优': "是" if is_group_best else "否"
            }
            all_rows.append(row)
        
        # 比较总伤害
        print(f"=== {weapon_name} + {set_name} 配置两轮总伤害对比 ===")
        for config_name, data in results.items():
            diff = data['total_dmg_both_rounds'] - best_in_group[1]['total_dmg_both_rounds']
            print(f"{config_name}: {data['total_dmg_both_rounds']:.2f} (差异: {diff:+.2f})")
        
        print(f"\n最优配置: {best_in_group[0]} (两轮总伤害: {best_in_group[1]['total_dmg_both_rounds']:.2f})")
        print("=" * 85)
    
    # 全局比较
    print("\n=== 全局配置两轮总伤害对比 ===")
    for row in all_rows:
        if abs(float(row['两轮总伤害']) - global_best_dmg) < 1:
            print(f"全局最优配置: {row['武器']} + {row['圣遗物套装']} ({row['主词条配置']}) | 两轮总伤害: {row['两轮总伤害']}")
    
    print("=" * 85)
    
    # 写入CSV文件
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\n结果已导出到: {csv_filename}")

if __name__ == "__main__":
    main()