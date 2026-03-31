/**
 * 上古必斩必杀 安全情报功能
 */

const securityTools = [
  {
    id: 'ip',
    name: 'IP归属地查询',
    desc: '查询IP地址的归属地、运营商等信息',
    url: 'https://ip.chinaz.com/',
    placeholder: '输入IP地址...'
  },
  {
    id: 'whois',
    name: 'WHOIS查询',
    desc: '查询域名的注册信息、过期时间等',
    url: 'https://whois.chinaz.com/',
    placeholder: '输入域名...'
  },
  {
    id: 'cve',
    name: 'CVE漏洞查询',
    desc: '查询CVE漏洞编号获取详细信息',
    urls: [
      { name: 'CVE Details', url: 'https://www.cvedetails.com/' },
      { name: '阿里云漏洞库', url: 'https://avd.aliyun.com/' }
    ],
    placeholder: '输入CVE编号，如CVE-2024-0001'
  },
  {
    id: 'site',
    name: '网站安全检测',
    desc: '检测网站安全状况、漏洞等',
    url: 'https://defense.yunaq.com/',
    placeholder: '输入网站地址...'
  }
];

function queryIP() {
  const ip = $securityIpInput.value.trim();
  if (!ip) {
    alert('请输入IP地址');
    return;
  }
  window.open('https://ip.chinaz.com/' + ip, '_blank');
}

function queryWhois() {
  const domain = $securityDomainInput.value.trim();
  if (!domain) {
    alert('请输入域名');
    return;
  }
  let finalDomain = domain;
  if (!domain.startsWith('http')) {
    finalDomain = 'http://' + domain;
  }
  const hostname = new URL(finalDomain).hostname;
  window.open('https://whois.chinaz.com/' + hostname, '_blank');
}

function queryCVE() {
  const cve = $securityCveInput.value.trim();
  if (!cve) {
    alert('请输入CVE编号');
    return;
  }
  const cveId = cve.toUpperCase();
  if (!cveId.startsWith('CVE-')) {
    alert('请输入有效的CVE编号，格式如：CVE-2024-0001');
    return;
  }
  window.open('https://avd.aliyun.com/search?keyword=' + cveId, '_blank');
}

function querySite() {
  const site = $securitySiteInput.value.trim();
  if (!site) {
    alert('请输入网站地址');
    return;
  }
  let url = site;
  if (!site.startsWith('http')) {
    url = 'http://' + site;
  }
  try {
    const hostname = new URL(url).hostname;
    window.open('https://tool.chinaz.com/webscan?host=' + hostname, '_blank');
  } catch (e) {
    alert('请输入有效的网站地址');
  }
}