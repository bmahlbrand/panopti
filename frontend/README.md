To set up development workflow locally:

In Terminal 1:
```bash
cd frontend/
npm run dev
```

In Terminal 2 run Panopti server with dev flag:
```bash
VITE_DEV_SERVER=1 python -m panopti.run_server --host localhost --port 8080 --debug --config ./.panopti.toml
```

In Terminal 3 run your Panopti script
```bash
python -m examples.test_all
```

This workflow supports hot reloading when modifying source code.