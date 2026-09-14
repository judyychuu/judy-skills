# Judy Skills

Judy 编写和维护的个人小工具与实验性 Agent Skills。

这些 Skills 主要用于验证工作流、沉淀个人方法和持续迭代。每个 Skill 都位于 `skills/` 下的独立目录中，至少包含一个 `SKILL.md`。

## Skills

| Skill | 说明 | 状态 |
| --- | --- | --- |
| [gift-recommender](skills/gift-recommender/) | 根据关系、场合、预算和生活方式推荐有品质、有发现感及能提升日常幸福感的礼物 | 实验性 |
| [image-to-pptx](skills/image-to-pptx/) | 图片转可编辑 PPTX，保留文字与 icon 比例，默认整数字号、微软雅黑、整体矢量 icon，并提供尺寸、字号与颜色结构检查工具 | 实验性 |

## 目录结构

```text
judy-skills/
├── README.md
└── skills/
    ├── image-to-pptx/
    │   ├── SKILL.md
    │   ├── agents/
    │   └── scripts/
    └── gift-recommender/
        ├── SKILL.md
        ├── README.md
        └── CHANGELOG.md
```

## 使用说明

进入具体 Skill 的目录查看安装方法、使用示例和版本记录。Release 中提供适合直接上传或安装的打包文件。

`image-to-pptx`：将整个 `skills/image-to-pptx` 目录复制到本机 `~/.codex/skills/`，提供图片后说“转ppt”即可调用。具体规则见其 `SKILL.md`；颜色整理脚本依赖 Python 的 `lxml`。

## License

本仓库采用 [MIT License](LICENSE)。
