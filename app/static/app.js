document.addEventListener('alpine:init', () => {
    Alpine.data('videoPlayer', ({ hasIntro, ambient }) => ({
        hasIntro,
        ambient,
        phase: hasIntro ? 'intro' : 'ambient',

        onEnded() {
            if (this.phase === 'intro' && this.ambient) {
                this.phase = 'ambient';
                const player = this.$refs.player;
                player.src = this.ambient;
                player.loop = true;
                player.load();
                player.play().catch(() => {});
            }
        },
    }));
});
