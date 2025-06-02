# Docker Platform Configuration

## IMPORTANT: Platform Settings for AWS ECS Deployment

All Docker builds in this project MUST target the `linux/amd64` platform for AWS ECS compatibility.

### Why This Matters

- Development machines (Apple Silicon Macs) use ARM64 architecture
- AWS ECS runs on AMD64 architecture
- Without explicit platform specification, Docker builds native images that won't run on ECS

### Configuration Applied

1. **Environment Variable**: `DOCKER_DEFAULT_PLATFORM=linux/amd64`
2. **Dockerfiles**: Use `--platform=linux/amd64` in FROM statements
3. **Build Commands**: Always include `--platform linux/amd64`
4. **Makefiles**: Platform configuration at the top of each service Makefile

### Usage Examples

```bash
# Build for deployment (linux/amd64)
docker build --platform linux/amd64 -t service-name .

# Or use the Makefile
make docker-build

# The platform is already configured in Makefiles
```

### Local Development

When running containers locally on ARM Macs, you'll see a warning:
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

This is expected and safe to ignore for local testing. The container will run under emulation.

### GitHub Actions

The deployment workflows automatically build for the correct platform since they run on AMD64 runners.