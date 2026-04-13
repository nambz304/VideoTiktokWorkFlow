.PHONY: backend frontend start

backend:
	cd backend && uvicorn main:app --reload

frontend:
	cd frontend && npm run dev

start:
	@echo "Start backend:  make backend"
	@echo "Start frontend: make frontend"
	@echo "Run both in separate terminals."

dev:
	@trap 'kill 0' SIGINT; \
	(cd backend && uvicorn main:app --reload) & \
	(cd frontend && npm run dev) & \
	wait