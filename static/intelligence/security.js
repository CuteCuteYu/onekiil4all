/**
 * 上古必斩必杀 安全情报功能
 */

// IPv4 校验
function isValidIPv4(ip) {
  const parts = ip.split('.');
  if (parts.length !== 4) return false;
  return parts.every(p => /^\d{1,3}$/.test(p) && parseInt(p) <= 255);
}

// IPv6 粗校验（十六进制与冒号组成）
function isValidIPv6(ip) {
  return /^[0-9a-fA-F:]+$/.test(ip) && ip.includes(':');
}

/**
 * 从输入中提取主机名。
 * 用 includes('://') 判断是否已带协议，
 * 避免把 httpfoo.com 这类以 http 开头的域名误判跳过补协议。
 */
function extractHostname(input) {
  const url = input.includes('://') ? input : `http://${input}`;
  return new URL(url).hostname;
}

function openExternal(url) {
  // noopener 防止新标签页通过 window.opener 反向操控本页（reverse tabnabbing）
  window.open(url, '_blank', 'noopener,noreferrer');
}

function queryIP() {
  const ip = $securityIpInput.value.trim();
  if (!ip) {
    alert('请输入IP地址');
    return;
  }
  if (!isValidIPv4(ip) && !isValidIPv6(ip)) {
    alert('请输入有效的IP地址，如 8.8.8.8');
    return;
  }
  openExternal('https://ip.chinaz.com/' + encodeURIComponent(ip));
}

function queryWhois() {
  const domain = $securityDomainInput.value.trim();
  if (!domain) {
    alert('请输入域名');
    return;
  }
  try {
    const hostname = extractHostname(domain);
    if (!hostname) throw new Error('empty hostname');
    openExternal('https://whois.chinaz.com/' + encodeURIComponent(hostname));
  } catch (e) {
    alert('请输入有效的域名');
  }
}

function queryCVE() {
  const cve = $securityCveInput.value.trim();
  if (!cve) {
    alert('请输入CVE编号');
    return;
  }
  const cveId = cve.toUpperCase();
  if (!/^CVE-\d{4}-\d{4,}$/.test(cveId)) {
    alert('请输入有效的CVE编号，格式如：CVE-2024-0001');
    return;
  }
  // 阿里云漏洞库搜索参数为 q（keyword 会得到"参数为空"错误页）
  openExternal('https://avd.aliyun.com/search?q=' + encodeURIComponent(cveId));
}

function querySite() {
  const site = $securitySiteInput.value.trim();
  if (!site) {
    alert('请输入网站地址');
    return;
  }
  try {
    const hostname = extractHostname(site);
    if (!hostname) throw new Error('empty hostname');
    openExternal('https://tool.chinaz.com/webscan?host=' + encodeURIComponent(hostname));
  } catch (e) {
    alert('请输入有效的网站地址');
  }
}
