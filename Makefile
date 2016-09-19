# Targets

TEST_DIR=test

test: build ftpUpload

build:
	@echo === Build Server ===	

ftpUpload:
	@echo === ftpUpload ===
	@rem python3 ftp_upload_process.py $(FTP_UPLOAD_PROCESS_ENV_FILE)