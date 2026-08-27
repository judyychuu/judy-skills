# Gift Recommender

一个兼容 Claude、Claude Code 和 Codex 的中文礼物推荐 Skill。它以自然、克制的“闺蜜式”沟通方式，根据收礼人、关系、场合、预算和禁忌进行分析，并给出分层推荐、避雷提示、送礼时可以说的话以及贺卡文案。

## 主要能力

- 根据关系亲疏与送礼场合判断推荐侧重点
- 按“首选 / 备选 / 预算升级”组织建议
- 关注孕期、产后、宠物、过敏和容貌焦虑等避雷因素
- 推荐具体品牌、商品、参考价格及购买渠道
- 发现对方不会主动升级、但能持续提升日常幸福感的高频小物
- 提供自然口语化的送礼表达
- 根据关系选择克制留白或温暖直接的贺卡文案

## 安装与使用

### Claude

从 [Releases](https://github.com/judyychuu/judy-skills/releases) 下载 `gift-recommender.zip`，然后在 Claude 的 `Customize > Skills` 中选择上传 Skill。

### Claude Code

从本仓库下载 `skills/gift-recommender` 目录，并复制到 Claude Code 的 Skills 目录：

```bash
cp -R skills/gift-recommender ~/.claude/skills/gift-recommender
```

### Codex

从本仓库下载 `skills/gift-recommender` 目录，并复制到 Codex 的个人 Skills 目录：

```bash
cp -R skills/gift-recommender ~/.codex/skills/gift-recommender
```

安装后重新开始一轮对话即可使用。

## 使用示例

```text
帮我给一位 30 岁左右的女性朋友挑生日礼物。她喜欢咖啡、家居设计，
家里养猫，预算 500～800 元。我们关系不错，但还没有到闺蜜的程度。
```

如果信息不完整，Skill 会优先询问缺失的关键信息，不会重复追问已经提供的内容。

## 文件说明

- `SKILL.md`：兼容 Agent Skills 结构的完整定义与工作流程
- `CHANGELOG.md`：版本更新记录

## 版本记录

查看 [CHANGELOG.md](CHANGELOG.md) 了解各版本的新增功能与调整。

## License

本 Skill 采用仓库根目录中的 [MIT License](../../LICENSE)。
