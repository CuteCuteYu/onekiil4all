/**
 * 上古必斩必杀 配置和常量
 */

const API = '';

const POLL_INTERVAL = 2000;

const MARKDOWN_OPTIONS = {
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true,
  gfm: true,
};

marked.setOptions(MARKDOWN_OPTIONS);