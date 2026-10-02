# WindCast Agent

WindCast Agent — система прогнозирования генерации ветропарка, которая переводит прогноз ветра в бизнес-решение: ожидаемую выработку, выручку, риск дисбаланса и рекомендацию для оператора.

Подробный рассказ для жюри: [docs/README.md](docs/README.md).

## Результат интерфейса

![WindCast AI dashboard](docs/dashboard-result.png)

## Почему это важно

Прогноз погоды не показывает, сколько энергии реально попадёт в сеть и сколько будет стоить ошибка. WindCast Agent объединяет исторические данные турбин, прогноз ветра и коммерческие параметры, чтобы заранее подготовить план поставки и резерв.

## Что умеет продукт

- прогнозировать мощность по двум турбинам на 24 или 48 часов;
- проверять качество входных CSV-данных;
- калибровать power curve и показывать MAE/RMSE;
- рассчитывать выработку, выручку и потенциальный штраф;
- находить часы низкой уверенности и резкие изменения ветра;
- выдавать уровень риска и понятную операционную рекомендацию;
- объяснять прогноз через AI или надёжный детерминированный fallback;
- проверять модель на исторических данных через walk-forward simulation.

## Технологии

### Frontend

React `19.1.0`, React DOM `19.1.0`, TypeScript `~5.8.3`, Vite `^6.3.5`, React Router DOM `^7.18.4`, Axios `^1.8.4`, Tailwind CSS `^3.4.17`, i18next `^26.4.2`, react-i18next `^17.0.15`, lucide-react `^0.511.0`, `@radix-ui/react-slot ^1.2.3`, `class-variance-authority ^0.7.1`, `clsx ^2.1.1`, `tailwind-merge ^3.3.0`.

Инструменты: `@vitejs/plugin-react ^4.5.2`, ESLint `^9.29.0`, `@eslint/js ^9.29.0`, `typescript-eslint ^8.34.0`, `eslint-plugin-react-hooks ^5.2.0`, `eslint-plugin-react-refresh ^0.4.20`, `@types/node ^22.15.30`, `@types/react ^19.1.8`, `@types/react-dom ^19.1.6`, PostCSS `^8.5.4`, Autoprefixer `^10.4.21`, `globals ^15.15.0`.

### Backend

Express `^5.1.0`, CORS `^2.8.5`, dotenv `^16.5.0`, Multer `^2.4.0`, TypeScript `^5.8.3`, встроенный Node.js SQLite, Open-Meteo Single Runs API и OpenAI Responses API.

Инструменты: `tsx ^4.19.4`, `@types/cors ^2.8.17`, `@types/express ^5.0.1`, `@types/multer ^2.2.0`, `@types/node ^22.15.30`.

## Запуск проекта

Frontend и backend запускаются в отдельных терминалах:

```bash
cd frontend
npm install
npm run dev
```

```bash
cd backend
npm install
copy .env.example .env
npm run dev
```

Конфигурация берётся из примеров:

- [backend/.env.example](backend/.env.example) — порт, координаты турбин, OpenAI, Open-Meteo и коммерческие значения;
- [frontend/.env.example](frontend/.env.example) — адрес backend через `VITE_API_URL`.

Frontend: `http://localhost:5173`
API: `http://localhost:3000/api/health`

## API

Основной бизнес-результат возвращает `POST /api/wind-farm/business-impact`. Остальные маршруты и формат ответа описаны в [docs/README.md](docs/README.md).

Не добавляйте `.env`, API-ключи и другие секреты в Git.
