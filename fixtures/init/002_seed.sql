INSERT INTO articles (
    external_id, title, summary, platform, source_type, author, url,
    published_at, sentiment, negative_score, severity, tags,
    likes, comments, shares, favorites
) VALUES
    ('bili-001', '“猜你不喜欢”入口调整引发讨论', '用户发现负反馈入口层级变化，担心表达不喜欢变得更困难。', 'B站', 'social', '数码观察员', 'https://fixture.invalid/bili-001', '2026-03-17 09:10:00+08', 'negative', 3, 'medium', ARRAY['bilibili-dislike', 'algorithm'], 1200, 380, 210, 95),
    ('bili-002', '产品界面正在进行小范围测试', '部分用户看到不同版本，尚不能确认是否为全量调整。', '微博', 'social', '产品动态', 'https://fixture.invalid/bili-002', '2026-03-17 14:30:00+08', 'neutral', NULL, NULL, ARRAY['bilibili-dislike'], 530, 120, 80, 20),
    ('bili-003', '用户质疑平台弱化负反馈机制', '讨论认为减少负反馈入口可能影响推荐透明度和用户控制感。', '知乎', 'social', '互联网研究社', 'https://fixture.invalid/bili-003', '2026-03-18 11:00:00+08', 'negative', 4, 'high', ARRAY['bilibili-dislike', 'algorithm'], 860, 290, 160, 110),
    ('bili-004', '推荐系统产品经理解读交互变化', '文章分析入口调整可能用于降低误触，但需要更清楚的用户说明。', '新闻', 'media', '科技前线', 'https://fixture.invalid/bili-004', '2026-03-18 17:40:00+08', 'neutral', NULL, NULL, ARRAY['bilibili-dislike'], 210, 75, 55, 15),
    ('bili-005', '“不喜欢”不是多余按钮', '评论集中表达对选择权被削弱的不满，并要求恢复原入口。', '微博', 'social', '新媒体评论', 'https://fixture.invalid/bili-005', '2026-03-19 08:50:00+08', 'negative', 4, 'high', ARRAY['bilibili-dislike'], 2100, 640, 390, 180),
    ('bili-006', '平台回应称将持续观察用户反馈', '回应承认处于实验阶段，并表示会结合数据与反馈评估方案。', '新闻', 'media', '商业报道', 'https://fixture.invalid/bili-006', '2026-03-19 19:20:00+08', 'positive', NULL, NULL, ARRAY['bilibili-dislike', 'official-response'], 450, 90, 130, 35),
    ('bili-007', '话题登上热搜后争议扩大', '大量转发将事件描述为平台不愿听取负面反馈，情绪明显升温。', '微博', 'social', '热点追踪', 'https://fixture.invalid/bili-007', '2026-03-20 10:05:00+08', 'negative', 5, 'critical', ARRAY['bilibili-dislike'], 5200, 1800, 2600, 420),
    ('bili-008', '不同客户端版本的入口实测', '实测显示多个版本存在差异，部分入口移动但功能没有完全消失。', 'B站', 'social', '体验实验室', 'https://fixture.invalid/bili-008', '2026-03-20 13:15:00+08', 'neutral', NULL, NULL, ARRAY['bilibili-dislike'], 980, 310, 170, 140),
    ('bili-009', '争议背后是用户对算法控制感的焦虑', '报道归纳用户担忧：推荐原因不透明、纠偏成本增加、反馈是否生效。', '新闻', 'media', '深度科技', 'https://fixture.invalid/bili-009', '2026-03-20 20:45:00+08', 'negative', 4, 'high', ARRAY['bilibili-dislike', 'algorithm'], 760, 240, 280, 85),
    ('bili-010', '部分测试用户称入口已经恢复', '用户截图显示原有入口重新出现，对快速调整表示认可。', 'B站', 'social', '社区记录员', 'https://fixture.invalid/bili-010', '2026-03-21 16:25:00+08', 'positive', NULL, NULL, ARRAY['bilibili-dislike'], 1400, 330, 260, 150),
    ('bili-011', '入口恢复后仍需解释实验目的', '负面讨论回落，但用户继续要求平台说明实验范围和反馈机制。', '微博', 'social', '舆情笔记', 'https://fixture.invalid/bili-011', '2026-03-22 12:10:00+08', 'negative', 2, 'medium', ARRAY['bilibili-dislike'], 1100, 270, 190, 75),
    ('bili-012', '事件热度下降，透明度诉求保留', '讨论量趋缓，核心诉求从恢复入口转向公开推荐与实验规则。', 'B站', 'social', '社区周报', 'https://fixture.invalid/bili-012', '2026-03-23 18:00:00+08', 'negative', 2, 'low', ARRAY['bilibili-dislike'], 670, 160, 95, 60),
    ('outside-001', '更早的相关讨论', '这条记录用于验证起始日期过滤。', 'B站', 'social', '边界测试', 'https://fixture.invalid/outside-001', '2026-03-16 23:59:59+08', 'negative', 2, 'low', ARRAY['bilibili-dislike'], 1, 1, 1, 1),
    ('outside-002', '同日无关话题', '这条记录用于验证标签过滤。', '微博', 'social', '边界测试', 'https://fixture.invalid/outside-002', '2026-03-20 12:00:00+08', 'negative', 3, 'medium', ARRAY['other-topic'], 9999, 9999, 9999, 9999),
    ('outside-003', '结束日之后的相关讨论', '这条记录用于验证结束日期过滤。', '新闻', 'media', '边界测试', 'https://fixture.invalid/outside-003', '2026-03-24 00:00:00+08', 'negative', 3, 'medium', ARRAY['bilibili-dislike'], 1, 1, 1, 1);
