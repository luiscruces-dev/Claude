// Imprime maqueta_plantillas.html a PDF a tamaño real con el Chromium de Playwright.
// Uso: node imprimir_pdf.js   (con PW_PATH apuntando a playwright si no esta en node_modules)
const path = require('path');
const { chromium } = require(process.env.PW_PATH || 'playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(__dirname, 'maqueta_plantillas.html'));
  await page.pdf({ path: path.resolve(__dirname, 'maqueta_plantillas.pdf'), printBackground: true, preferCSSPageSize: true });
  await browser.close();
  console.log('Escrito: maqueta_plantillas.pdf');
})();
