<template>
    <div class="home">
        <!-- Hero Section -->
        <section class="hero-section">
            <div class="hero-bg"></div>
            <div class="container position-relative">
                <div class="row min-vh-100 align-items-center">
                    <div class="col-lg-7 col-xl-6">
                        <div class="hero-content">
                            <span class="hero-badge animate-fade-in-up">
                                <i class="bi bi-lightning-charge me-1"></i>
                                Farm-to-retail traceability
                            </span>
                            <h1
                                class="hero-title animate-fade-in-up animate-delay-1"
                            >
                                Streamline your
                                <span class="text-accent">agricultural</span>
                                operations
                            </h1>
                            <p
                                class="hero-subtitle animate-fade-in-up animate-delay-2"
                            >
                                Track produce through every processing stage —
                                from harvest to retail shelf. Batch lineage,
                                FIFO costing, and full operational visibility in
                                one platform.
                            </p>
                            <div
                                class="d-flex flex-column flex-sm-row gap-3 animate-fade-in-up animate-delay-3"
                            >
                                <RouterLink
                                    :to="
                                        auth.isAuthenticated
                                            ? '/dashboard'
                                            : '/register'
                                    "
                                    class="btn btn-moss btn-lg px-4 rounded-pill"
                                >
                                    <i class="bi bi-arrow-right me-2"></i>Start
                                    tracking
                                </RouterLink>
                                <a
                                    href="#features"
                                    class="btn btn-outline-moss btn-lg px-4 rounded-pill"
                                    @click.prevent="scrollTo('features')"
                                >
                                    Learn more
                                </a>
                            </div>
                        </div>
                    </div>
                    <div
                        class="col-lg-5 col-xl-6 d-none d-lg-flex justify-content-center"
                    >
                        <div
                            class="hero-visual animate-fade-in animate-delay-3"
                        >
                            <div class="visual-card">
                                <div class="visual-card-header">
                                    <span class="dot dot-green"></span>
                                    <span class="dot dot-amber"></span>
                                    <span class="dot dot-red"></span>
                                </div>
                                <div class="visual-card-body">
                                    <div
                                        class="visual-row"
                                        v-for="(stage, i) in stages.slice(0, 4)"
                                        :key="i"
                                        :style="{
                                            animationDelay: `${0.5 + i * 0.1}s`,
                                        }"
                                    >
                                        <i class="bi" :class="stage.icon"></i>
                                        <span class="visual-label">{{
                                            stage.label
                                        }}</span>
                                        <span class="visual-bar">
                                            <span
                                                class="visual-fill"
                                                :style="{
                                                    width: `${90 - i * 15}%`,
                                                }"
                                            ></span>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features/Stages Section -->
        <section id="features" class="features-section py-5">
            <div class="container py-5">
                <div class="text-center mb-5">
                    <span class="section-tag animate-fade-in-up"
                        >Processing Pipeline</span
                    >
                    <h2
                        class="section-title animate-fade-in-up animate-delay-1"
                    >
                        Custom stages, total control
                    </h2>
                    <p
                        class="section-desc mx-auto animate-fade-in-up animate-delay-2"
                    >
                        Every kilogram tracked from field to customer with full
                        batch lineage and cost allocation.
                    </p>
                </div>

                <div class="row g-4">
                    <div
                        v-for="(stage, i) in stages"
                        :key="stage.label"
                        class="col-md-6 col-lg-4"
                    >
                        <div
                            class="stage-card animate-fade-in-up"
                            :style="{ animationDelay: `${0.1 * i}s` }"
                        >
                            <div class="stage-icon-wrap">
                                <i class="bi" :class="stage.icon"></i>
                            </div>
                            <div>
                                <h5 class="stage-label">{{ stage.label }}</h5>
                                <p class="stage-desc">{{ stage.desc }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Capabilities -->
        <section class="capabilities-section py-5">
            <div class="container py-5">
                <div class="row align-items-center g-5">
                    <div class="col-lg-5">
                        <span class="section-tag animate-fade-in-up"
                            >Why AgriFlow</span
                        >
                        <h2
                            class="section-title animate-fade-in-up animate-delay-1"
                        >
                            Built for agricultural precision
                        </h2>
                        <p
                            class="text-secondary animate-fade-in-up animate-delay-2"
                        >
                            Purpose-built tools for farms and processing units
                            that need accurate batch tracking, cost management,
                            and operational oversight.
                        </p>
                    </div>
                    <div class="col-lg-7">
                        <div class="row g-3">
                            <div class="col-sm-6">
                                <div
                                    class="cap-card animate-fade-in-up animate-delay-2"
                                >
                                    <i class="bi bi-diagram-3 cap-icon"></i>
                                    <h6>Batch Lineage</h6>
                                    <p>
                                        Full parent-child batch trees track
                                        material splitting and transformation.
                                    </p>
                                </div>
                            </div>
                            <div class="col-sm-6">
                                <div
                                    class="cap-card animate-fade-in-up animate-delay-3"
                                >
                                    <i class="bi bi-calculator cap-icon"></i>
                                    <h6>FIFO Costing</h6>
                                    <p>
                                        Automatic cost allocation using
                                        first-in, first-out purchase lot
                                        tracking.
                                    </p>
                                </div>
                            </div>
                            <div class="col-sm-6">
                                <div
                                    class="cap-card animate-fade-in-up animate-delay-4"
                                >
                                    <i class="bi bi-clock-history cap-icon"></i>
                                    <h6>Cost Freezing</h6>
                                    <p>
                                        Rates frozen at event time so historical
                                        records stay accurate forever.
                                    </p>
                                </div>
                            </div>
                            <div class="col-sm-6">
                                <div
                                    class="cap-card animate-fade-in-up animate-delay-5"
                                >
                                    <i class="bi bi-people cap-icon"></i>
                                    <h6>Team Tracking</h6>
                                    <p>
                                        Personnel, vehicles, and assets tied to
                                        every processing event.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA -->
        <section class="cta-section py-5">
            <div class="container py-5 text-center">
                <h2 class="cta-title animate-fade-in-up">
                    Ready to modernize your operations?
                </h2>
                <p class="cta-desc mx-auto animate-fade-in-up animate-delay-1">
                    Start tracking your produce pipeline today. Set up takes
                    minutes.
                </p>
                <RouterLink
                    to="/register"
                    class="btn btn-lg btn-moss px-5 rounded-pill animate-fade-in-up animate-delay-2"
                >
                    Get started free
                </RouterLink>
            </div>
        </section>

        <!-- Footer -->
        <footer class="site-footer py-4">
            <div
                class="container d-flex flex-column flex-sm-row justify-content-between align-items-center gap-2"
            >
                <span class="footer-brand">
                    <i class="bi bi-tree me-1"></i>AgriFlow
                </span>
                <span class="text-secondary" style="font-size: 0.82rem">
                    &copy; 2026 AgriFlow. Built for farmers.
                </span>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const stages = [
    {
        icon: "bi-flower1",
        label: "Harvest",
        desc: "Track raw material collection from plantations",
    },
    {
        icon: "bi-droplet",
        label: "Clean",
        desc: "Record washing and cleaning processes",
    },
    {
        icon: "bi-sun",
        label: "Dry",
        desc: "Monitor drying cycles and conditions",
    },
    {
        icon: "bi-bag",
        label: "Bag & Grade",
        desc: "Batch grading and quality classification",
    },
    {
        icon: "bi-box2",
        label: "Pack",
        desc: "Package produce with full batch traceability",
    },
    {
        icon: "bi-shop",
        label: "Retail",
        desc: "Track sales with FIFO costing and allocation",
    },
];

const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
};
</script>

<style scoped>
/* ---- Hero ---- */
.hero-section {
    position: relative;
    overflow: hidden;
    background: var(--bg-primary);
}

.hero-bg {
    position: absolute;
    inset: 0;
    background:
        radial-gradient(
            ellipse 70% 50% at 80% 20%,
            rgba(74, 103, 65, 0.06) 0%,
            transparent 60%
        ),
        radial-gradient(
            ellipse 50% 60% at 10% 80%,
            rgba(181, 105, 77, 0.04) 0%,
            transparent 50%
        );
    pointer-events: none;
}

.hero-content {
    padding: 120px 0 80px;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    background: var(--moss-faded);
    color: var(--moss);
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 24px;
    letter-spacing: 0.02em;
}

.hero-title {
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 5vw, 3.5rem);
    line-height: 1.12;
    margin-bottom: 20px;
    color: var(--loam);
}

.hero-title .text-accent {
    color: var(--moss);
}

.hero-subtitle {
    font-size: 1.08rem;
    color: var(--text-secondary);
    max-width: 480px;
    line-height: 1.7;
    margin-bottom: 32px;
}

/* Hero visual card */
.hero-visual {
    perspective: 800px;
}

.visual-card {
    width: 320px;
    background: var(--white);
    border-radius: 16px;
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    transform: rotateY(-4deg) rotateX(2deg);
    transition: transform 0.4s var(--ease-out);
}

.visual-card:hover {
    transform: rotateY(0deg) rotateX(0deg);
}

.visual-card-header {
    display: flex;
    gap: 6px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-light);
}

.dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.dot-green {
    background: var(--moss);
}
.dot-amber {
    background: var(--harvest);
}
.dot-red {
    background: var(--sienna);
}

.visual-card-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.visual-row {
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeInUp 0.4s var(--ease-out) both;
}

.visual-row i {
    color: var(--moss);
    font-size: 1rem;
    width: 20px;
    text-align: center;
}

.visual-label {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-primary);
    width: 60px;
}

.visual-bar {
    flex: 1;
    height: 6px;
    background: var(--parchment-deep);
    border-radius: 3px;
    overflow: hidden;
}

.visual-fill {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, var(--moss), var(--sage));
    border-radius: 3px;
    transition: width 1s var(--ease-out);
}

/* ---- Sections ---- */
.section-tag {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--sienna);
    margin-bottom: 12px;
}

.section-title {
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 3.5vw, 2.4rem);
    margin-bottom: 12px;
}

.section-desc {
    color: var(--text-secondary);
    max-width: 520px;
    font-size: 1.02rem;
    line-height: 1.65;
}

/* Stage cards */
.stage-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    transition: all var(--transition-fast);
    height: 100%;
}

.stage-card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--sage-light);
}

.stage-icon-wrap {
    width: 44px;
    height: 44px;
    background: var(--moss-faded);
    color: var(--moss);
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}

.stage-label {
    font-family: var(--font-display);
    font-size: 1.05rem;
    margin-bottom: 4px;
}

.stage-desc {
    font-size: 0.86rem;
    color: var(--text-secondary);
    margin-bottom: 0;
    line-height: 1.55;
}

/* Capabilities */
.capabilities-section {
    background: var(--parchment-deep);
}

.cap-card {
    padding: 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    height: 100%;
    transition: all var(--transition-fast);
}

.cap-card:hover {
    box-shadow: var(--shadow-md);
}

.cap-icon {
    font-size: 1.5rem;
    color: var(--sienna);
    margin-bottom: 12px;
    display: block;
}

.cap-card h6 {
    font-family: var(--font-display);
    font-size: 1rem;
    margin-bottom: 6px;
}

.cap-card p {
    font-size: 0.84rem;
    color: var(--text-secondary);
    margin-bottom: 0;
    line-height: 1.55;
}

/* CTA */
.cta-section {
    background: var(--bg-primary);
}

.cta-title {
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 3vw, 2.2rem);
    margin-bottom: 12px;
}

.cta-desc {
    color: var(--text-secondary);
    max-width: 460px;
    margin-bottom: 28px;
}

/* Footer */
.site-footer {
    border-top: 1px solid var(--border-light);
}

.footer-brand {
    font-family: var(--font-display);
    font-size: 1.05rem;
    color: var(--loam);
}

/* ---- Responsive ---- */
@media (max-width: 991.98px) {
    .hero-content {
        padding: 80px 0 60px;
    }

    .capabilities-section .col-lg-5 {
        text-align: center;
    }
}

@media (max-width: 767.98px) {
    .hero-content {
        padding: 48px 0 40px;
        text-align: center;
    }

    .hero-subtitle {
        margin-left: auto;
        margin-right: auto;
    }

    .hero-badge {
        margin-bottom: 16px;
    }

    .features-section .container,
    .capabilities-section .container,
    .cta-section .container {
        padding-top: 24px !important;
        padding-bottom: 24px !important;
    }

    .stage-card {
        padding: 18px;
        gap: 12px;
    }

    .stage-icon-wrap {
        width: 38px;
        height: 38px;
        font-size: 1.05rem;
    }

    .cap-card {
        padding: 18px;
    }
}

@media (max-width: 575.98px) {
    .hero-content {
        padding: 36px 0 32px;
    }

    .hero-title {
        font-size: 1.75rem;
    }

    .hero-subtitle {
        font-size: 0.95rem;
    }

    .section-title {
        font-size: 1.4rem;
    }

    .cta-title {
        font-size: 1.4rem;
    }
}
</style>
